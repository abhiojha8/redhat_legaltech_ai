"""
Call Data Analysis Service for penalty detection and compliance checking.
"""

import pandas as pd
import os
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from dotenv import load_dotenv

class CallDataService:
    """Service for analyzing call data and detecting potential penalties."""
    
    def __init__(self):
        """Initialize the call data service."""
        load_dotenv()
        self.supported_columns = [
            'call_id', 'caller_number', 'callee_number', 'call_duration', 
            'call_time', 'call_type', 'location', 'network_type'
        ]
        
    def process_excel_file(self, uploaded_file) -> Dict[str, Any]:
        """Process uploaded Excel file and extract call data."""
        try:
            # Reset file pointer
            uploaded_file.seek(0)
            
            # Read Excel file
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            
            # Basic data validation
            if df.empty:
                return {"success": False, "error": "Excel file is empty"}
            
            # Standardize column names (convert to lowercase and replace spaces)
            df.columns = df.columns.str.lower().str.replace(' ', '_')
            
            # Data quality check
            quality_issues = self._check_data_quality(df)
            
            # Basic statistics
            stats = {
                "total_records": len(df),
                "columns": list(df.columns),
                "date_range": self._get_date_range(df),
                "data_types": df.dtypes.to_dict()
            }
            
            return {
                "success": True,
                "data": df,
                "stats": stats,
                "quality_issues": quality_issues
            }
            
        except Exception as e:
            return {"success": False, "error": f"Excel processing error: {str(e)}"}
    
    def _check_data_quality(self, df: pd.DataFrame) -> List[str]:
        """Check data quality and return list of issues."""
        issues = []
        
        # Check for missing values
        missing_counts = df.isnull().sum()
        for col, count in missing_counts.items():
            if count > 0:
                issues.append(f"Missing values in '{col}': {count} records")
        
        # Check for duplicate records
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            issues.append(f"Duplicate records found: {duplicates}")
        
        # Check for suspicious patterns
        if 'call_duration' in df.columns:
            # Very long calls (>2 hours)
            long_calls = df[df['call_duration'] > 7200].shape[0]
            if long_calls > 0:
                issues.append(f"Unusually long calls (>2 hours): {long_calls}")
                
            # Very short calls (<1 second)
            short_calls = df[df['call_duration'] < 1].shape[0]
            if short_calls > 0:
                issues.append(f"Very short calls (<1 second): {short_calls}")
        
        return issues
    
    def _get_date_range(self, df: pd.DataFrame) -> Dict[str, str]:
        """Extract date range from call data."""
        date_columns = ['call_time', 'timestamp', 'date', 'call_date']
        
        for col in date_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                    min_date = df[col].min()
                    max_date = df[col].max()
                    return {
                        "start_date": min_date.strftime("%Y-%m-%d") if pd.notna(min_date) else "Unknown",
                        "end_date": max_date.strftime("%Y-%m-%d") if pd.notna(max_date) else "Unknown",
                        "duration_days": (max_date - min_date).days if pd.notna(min_date) and pd.notna(max_date) else 0
                    }
                except:
                    continue
        
        return {"start_date": "Unknown", "end_date": "Unknown", "duration_days": 0}
    
    def _analyze_call_drops(self, df: pd.DataFrame) -> Dict[str, List]:
        """Comprehensive TRAI call drop analysis with 2024 penalty structure."""
        violations = {"high_risk": [], "medium_risk": [], "low_risk": []}
        
        # Method 1: Direct call drop count analysis (most accurate)
        if 'call_drop_cnt_d' in df.columns and 'tot_call_cnt_d' in df.columns:
            # Calculate actual call drop rate from the data
            total_calls = df['tot_call_cnt_d'].sum()
            total_drops = df['call_drop_cnt_d'].sum()
            drop_rate = (total_drops / total_calls) * 100 if total_calls > 0 else 0
            
            # Count customers with drops
            customers_with_drops = len(df[df['call_drop_cnt_d'] > 0])
            
            # TRAI 2024 benchmark: 2% max call drop rate
            if drop_rate > 2.0:
                penalty_tier = self._get_drop_penalty_tier(drop_rate)
                violations["high_risk"].append({
                    "type": "TRAI Call Drop Rate Violation",
                    "count": total_drops,
                    "description": f"{total_drops} call drops out of {total_calls} total calls ({drop_rate:.2f}% rate)",
                    "customers_affected": customers_with_drops,
                    "trai_benchmark": "Maximum 2% allowed",
                    "violation_severity": f"{drop_rate:.2f}% exceeds TRAI limit by {drop_rate-2:.2f}%",
                    "penalty_range": penalty_tier["penalty"],
                    "penalty_calculation": penalty_tier["calculation"],
                    "regulation_ref": "TRAI QoS Standards 2024",
                    "sample_records": df[df['call_drop_cnt_d'] > 0].head(3)[['customer_id', 'service_area', 'tot_call_cnt_d', 'call_drop_cnt_d']].to_dict('records')
                })
            elif drop_rate > 1.5:
                violations["medium_risk"].append({
                    "type": "High Call Drop Rate (Warning)",
                    "count": total_drops,
                    "description": f"{total_drops} call drops ({drop_rate:.2f}% rate) - near TRAI limit",
                    "customers_affected": customers_with_drops,
                    "trai_benchmark": "Maximum 2% allowed",
                    "penalty_range": "₹50,000 - Warning level",
                    "regulation_ref": "TRAI QoS Standards 2024"
                })
            elif drop_rate > 1.0:
                violations["low_risk"].append({
                    "type": "Moderate Call Drop Rate",
                    "count": total_drops,
                    "description": f"{total_drops} call drops ({drop_rate:.2f}% rate) - acceptable but monitor",
                    "customers_affected": customers_with_drops,
                    "trai_benchmark": "Maximum 2% allowed",
                    "penalty_range": "No penalty - monitoring recommended"
                })
        
        # Method 2: Location-based drop analysis using service_area
        if 'service_area' in df.columns and 'call_drop_cnt_d' in df.columns:
            # Analyze drops by service area
            area_analysis = df.groupby('service_area').agg({
                'call_drop_cnt_d': 'sum',
                'tot_call_cnt_d': 'sum',
                'customer_id': 'count'
            }).reset_index()
            
            # Calculate drop rate per area
            area_analysis['drop_rate'] = (area_analysis['call_drop_cnt_d'] / area_analysis['tot_call_cnt_d']) * 100
            
            # Find areas exceeding TRAI 2% limit
            trai_violation_areas = area_analysis[area_analysis['drop_rate'] > 2.0]
            warning_areas = area_analysis[(area_analysis['drop_rate'] > 1.5) & (area_analysis['drop_rate'] <= 2.0)]
            
            if not trai_violation_areas.empty:
                worst_area = trai_violation_areas.iloc[0]
                penalty_tier = self._get_drop_penalty_tier(worst_area['drop_rate'])
                violations["high_risk"].append({
                    "type": "TRAI Service Area Drop Rate Violation",
                    "count": len(trai_violation_areas),
                    "description": f"{len(trai_violation_areas)} service areas exceed 2% TRAI limit (worst: {worst_area['service_area']} at {worst_area['drop_rate']:.2f}%)",
                    "trai_benchmark": "Maximum 2% per service area",
                    "penalty_range": penalty_tier["penalty"],
                    "penalty_calculation": f"Area-specific violations: {penalty_tier['calculation']}",
                    "regulation_ref": "TRAI QoS Standards 2024 - Area-wise compliance",
                    "areas_affected": trai_violation_areas[['service_area', 'drop_rate', 'call_drop_cnt_d']].to_dict('records')
                })
            
            if not warning_areas.empty:
                violations["medium_risk"].append({
                    "type": "Service Area Drop Rate Warning",
                    "count": len(warning_areas),
                    "description": f"{len(warning_areas)} service areas near TRAI limit (1.5-2.0% drop rate)",
                    "penalty_range": "₹50,000 - Monitoring required",
                    "areas_affected": warning_areas[['service_area', 'drop_rate', 'call_drop_cnt_d']].to_dict('records'),
                    "regulation_ref": "TRAI QoS Standards - Preventive monitoring"
                })
        
        # Method 3: Customer-level drop analysis
        if 'call_drop_cnt_d' in df.columns and 'tot_call_cnt_d' in df.columns:
            # Find customers with very high individual drop rates
            df['customer_drop_rate'] = (df['call_drop_cnt_d'] / df['tot_call_cnt_d']) * 100
            high_drop_customers = df[df['customer_drop_rate'] > 20]  # >20% individual drop rate
            
            if not high_drop_customers.empty:
                violations["medium_risk"].append({
                    "type": "Individual Customer Drop Issues",
                    "count": len(high_drop_customers),
                    "description": f"{len(high_drop_customers)} customers with >20% individual drop rates",
                    "penalty_range": "Service quality investigation required",
                    "regulation_ref": "TRAI Customer Protection Standards",
                    "sample_customers": high_drop_customers.head(3)[['customer_id', 'service_area', 'customer_drop_rate']].to_dict('records')
                })
        
        # Method 4: Legacy call duration-based analysis (fallback)
        if 'call_duration' in df.columns:
            # TRAI considers calls <3 seconds as potential drops
            potential_drops = df[df['call_duration'] < 3]
            drop_rate = (len(potential_drops) / len(df)) * 100 if len(df) > 0 else 0
            
            if drop_rate > 2.0:
                penalty_tier = self._get_drop_penalty_tier(drop_rate)
                violations["high_risk"].append({
                    "type": "Duration-based Call Drop Detection",
                    "count": len(potential_drops),
                    "description": f"{len(potential_drops)} calls <3 seconds ({drop_rate:.2f}% rate)",
                    "penalty_range": penalty_tier["penalty"],
                    "regulation_ref": "TRAI QoS Standards 2024"
                })
        
        return violations
    
    def _get_drop_penalty_tier(self, drop_rate: float) -> Dict[str, str]:
        """Calculate TRAI penalty tier based on call drop rate."""
        if drop_rate > 5.0:
            return {
                "penalty": "₹5-10 lakh (Severe violation)",
                "calculation": f"Drop rate {drop_rate:.2f}% - Tier 4 penalty (>5%)"
            }
        elif drop_rate > 4.0:
            return {
                "penalty": "₹2-5 lakh (High violation)", 
                "calculation": f"Drop rate {drop_rate:.2f}% - Tier 3 penalty (4-5%)"
            }
        elif drop_rate > 3.0:
            return {
                "penalty": "₹1-2 lakh (Medium violation)",
                "calculation": f"Drop rate {drop_rate:.2f}% - Tier 2 penalty (3-4%)"
            }
        else:  # 2-3%
            return {
                "penalty": "₹50,000-1 lakh (Base violation)",
                "calculation": f"Drop rate {drop_rate:.2f}% - Tier 1 penalty (2-3%)"
            }
    
    def analyze_compliance_violations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze call data for potential compliance violations."""
        violations = {
            "high_risk": [],
            "medium_risk": [],
            "low_risk": [],
            "summary": {}
        }
        
        try:
            # 1. TRAI Call Drop Analysis (Highest Priority)
            call_drop_violations = self._analyze_call_drops(df)
            violations["high_risk"].extend(call_drop_violations["high_risk"])
            violations["medium_risk"].extend(call_drop_violations["medium_risk"])
            violations["low_risk"].extend(call_drop_violations["low_risk"])
            
            # 2. Call Duration Analysis
            if 'call_duration' in df.columns:
                # Excessive call duration violations
                long_calls = df[df['call_duration'] > 3600]  # >1 hour
                if not long_calls.empty:
                    violations["high_risk"].append({
                        "type": "Excessive Call Duration",
                        "count": len(long_calls),
                        "description": f"{len(long_calls)} calls exceed 1 hour duration",
                        "max_duration": long_calls['call_duration'].max(),
                        "penalty_range": "₹1-2 lakh for service quality issues",
                        "regulation_ref": "TRAI QoS Standards 2024",
                        "sample_records": long_calls.head(3).to_dict('records')
                    })
            
            # 2. Call Frequency Analysis
            if 'caller_number' in df.columns:
                # High frequency calling patterns
                call_frequency = df['caller_number'].value_counts()
                high_freq_callers = call_frequency[call_frequency > 100]  # >100 calls
                
                if not high_freq_callers.empty:
                    violations["medium_risk"].append({
                        "type": "High Frequency Calling",
                        "count": len(high_freq_callers),
                        "description": f"{len(high_freq_callers)} numbers made >100 calls",
                        "top_caller": high_freq_callers.index[0],
                        "max_calls": high_freq_callers.iloc[0]
                    })
            
            # 3. Time Pattern Analysis
            if 'call_time' in df.columns:
                try:
                    df['call_time'] = pd.to_datetime(df['call_time'])
                    df['hour'] = df['call_time'].dt.hour
                    
                    # Calls outside business hours (before 8 AM or after 10 PM)
                    off_hours = df[(df['hour'] < 8) | (df['hour'] > 22)]
                    if not off_hours.empty:
                        violations["low_risk"].append({
                            "type": "Off-Hours Calling",
                            "count": len(off_hours),
                            "description": f"{len(off_hours)} calls made outside business hours (8 AM - 10 PM)",
                            "percentage": (len(off_hours) / len(df)) * 100
                        })
                except:
                    pass
            
            # 4. Data Quality Violations
            missing_data = df.isnull().sum().sum()
            if missing_data > 0:
                violations["low_risk"].append({
                    "type": "Data Quality Issues",
                    "count": missing_data,
                    "description": f"{missing_data} missing data points found",
                    "columns_affected": df.isnull().sum()[df.isnull().sum() > 0].to_dict()
                })
            
            # Generate TRAI-specific summary with penalty estimates
            high_penalty = len(violations["high_risk"]) * 300000  # ₹3 lakh average
            medium_penalty = len(violations["medium_risk"]) * 125000  # ₹1.25 lakh average
            low_penalty = len(violations["low_risk"]) * 50000  # ₹50,000 average
            
            # Check for call drop violations specifically
            call_drop_found = any("Drop" in v.get("type", "") for v in violations["high_risk"] + violations["medium_risk"])
            
            violations["summary"] = {
                "total_records_analyzed": len(df),
                "high_risk_count": len(violations["high_risk"]),
                "medium_risk_count": len(violations["medium_risk"]),
                "low_risk_count": len(violations["low_risk"]),
                "trai_compliance_score": max(0, 100 - (len(violations["high_risk"]) * 40 + len(violations["medium_risk"]) * 20 + len(violations["low_risk"]) * 10)),
                "estimated_penalty_inr": high_penalty + medium_penalty + low_penalty,
                "call_drop_violation_detected": call_drop_found,
                "regulatory_authority": "TRAI (Telecom Regulatory Authority of India)",
                "benchmark_year": "2024 QoS Standards",
                "key_trai_limits": {
                    "call_drop_rate": "Maximum 2%",
                    "penalty_range": "₹50,000 - ₹10 lakh (graded)",
                    "consecutive_violations": "1.5x to 2x penalty multiplier"
                }
            }
            
            return {"success": True, "violations": violations}
            
        except Exception as e:
            return {"success": False, "error": f"Compliance analysis error: {str(e)}"}
    
    def generate_analysis_prompt(self, violations: Dict[str, Any], context: str = "") -> str:
        """Generate a concise prompt for AI analysis of violations."""
        
        summary = violations.get("summary", {})
        
        # Build concise violation list
        violation_list = []
        for risk_level in ["high_risk", "medium_risk", "low_risk"]:
            for violation in violations.get(risk_level, []):
                violation_list.append(f"• {violation['type']}: {violation['description']}")
        
        prompt = f"""STRICT LIMIT: Respond in EXACTLY 150 words or less. No more.

TRAI Violations Found:
{chr(10).join(violation_list[:3])}

FORMAT (use exactly this structure):
**Penalties**: [List max 3 violations with INR amounts]
**Legal Basis**: [1 sentence - TRAI regulation reference]
**Actions**: [3 bullet points max 5 words each]
**Risk**: [1 sentence assessment]

STOP at 150 words. Do not exceed this limit under any circumstances."""
        
        return prompt
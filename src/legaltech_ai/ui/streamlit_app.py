"""
Simple Streamlit application for LegalTech AI.
"""

import streamlit as st
import os
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from watsonx_service import WatsonxService
from document_service import DocumentService
from call_data_service import CallDataService
import pandas as pd

# Load environment variables
load_dotenv()

def setup_page():
    """Setup Streamlit page configuration."""
    st.set_page_config(
        page_title="🧠 LegalTech AI",
        page_icon="⚖️",
        layout="wide"
    )
    
    st.markdown("<h1 style='text-align: center;'>🧠 LegalTech AI - Red Hat Hackathon</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'><strong>Powered by IBM watsonx.ai</strong></p>", unsafe_allow_html=True)
    st.markdown("---")

def document_upload_section():
    """Handle document upload and processing."""
    st.header("📄 Document Analysis")
    
    uploaded_file = st.file_uploader(
        "Upload a document (PDF, DOCX, TXT)",
        type=['pdf', 'docx', 'txt'],
        help="Maximum file size: 10MB"
    )
    
    if uploaded_file:
        # Reset file pointer to beginning
        uploaded_file.seek(0)
        
        # Simple text extraction
        try:
            if uploaded_file.type == "text/plain":
                text = str(uploaded_file.read(), "utf-8")
            elif uploaded_file.type == "application/pdf":
                try:
                    import pypdf
                    reader = pypdf.PdfReader(uploaded_file)
                    text = "\n".join([page.extract_text() for page in reader.pages])
                except ImportError:
                    st.error("📋 PDF processing requires pypdf. Install with: pip install pypdf")
                    return
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                try:
                    from docx import Document
                    doc = Document(uploaded_file)
                    text = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
                except ImportError:
                    st.error("📋 DOCX processing requires python-docx. Install with: pip install python-docx")
                    return
            else:
                st.error("❌ Unsupported file format")
                return
            
            if text.strip():
                # Initialize watsonx service
                watsonx_service = WatsonxService()
                
                # Analyze document
                with st.spinner("🧠 Analyzing with IBM watsonx.ai..."):
                    result = watsonx_service.analyze_document(text)
                
                if result['status'] == 'success':
                    st.success("✅ Analysis complete!")
                    st.info(f"📊 Document: {uploaded_file.name} ({result['document_length']:,} characters)")
                    
                    st.subheader("🎯 Legal Analysis")
                    st.write(result['analysis'])
                    
                else:
                    st.error(f"❌ Analysis failed: {result['error']}")
            else:
                st.warning("⚠️ Document appears to be empty")
                
        except Exception as e:
            st.error(f"❌ Error processing document: {str(e)}")

def chat_with_documents():
    """Handle chat functionality with document context."""
    st.header("💬 Legal Assistant Chat")
    
    # Initialize document service
    if "document_service" not in st.session_state:
        st.session_state.document_service = DocumentService()
    document_service = st.session_state.document_service
    
    # Document upload section for context
    with st.expander("📄 Upload Document for Context", expanded=False):
        context_file = st.file_uploader(
            "Upload document for intelligent context analysis",
            type=['pdf', 'docx', 'txt'],
            help="The AI will use this document to provide context-aware responses",
            key="context_file"
        )
        
        if context_file:
            with st.spinner("🔍 Processing document for context..."):
                # Reset file pointer
                context_file.seek(0)
                
                try:
                    # Extract text based on file type
                    if context_file.type == "text/plain":
                        document_text = str(context_file.read(), "utf-8")
                    elif context_file.type == "application/pdf":
                        import pypdf
                        reader = pypdf.PdfReader(context_file)
                        document_text = "\n".join([page.extract_text() for page in reader.pages])
                    elif context_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        from docx import Document
                        doc = Document(context_file)
                        document_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                    
                    if document_text.strip():
                        # Add to document service
                        result = document_service.add_document(document_text, context_file.name)
                        
                        if result["success"]:
                            if result.get('will_use_summary', False):
                                st.success("✅ Large document processed! Document will be summarized for context.")
                            else:
                                st.success("✅ Document processed! Full document will be used as context.")
                            st.info(f"📊 Document: {result['document_name']} ({len(document_text):,} characters)")
                        else:
                            st.error(f"❌ Document processing failed: {result['error']}")
                    else:
                        st.warning("⚠️ Document appears to be empty")
                        
                except Exception as e:
                    st.error(f"❌ Error processing document: {str(e)}")
    
    # Show document status
    if document_service.has_documents():
        st.success("🔍 Document Context: Active")
    else:
        st.warning("⚠️ No Document Context - Upload a document for context-aware responses")
    
    st.markdown("---")
    
    # Chat interface
    st.subheader("💬 Ask Your Legal Question")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a legal question..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response with document context
        with st.chat_message("assistant"):
            with st.spinner("🧠 IBM watsonx.ai is thinking..."):
                try:
                    # Get relevant context from document
                    if document_service.has_documents():
                        context = document_service.get_context_for_query(prompt)
                        
                        # Get response from watsonx
                        watsonx_service = WatsonxService()
                        result = watsonx_service.chat_response(prompt, context)
                        
                        if result['status'] == 'success':
                            response = result['response']
                            st.markdown(response)
                            st.caption("🔍 Answer based on document context")
                        else:
                            error_msg = f"❌ Error: {result['error']}"
                            st.error(error_msg)
                            response = error_msg
                    else:
                        # General response without context
                        watsonx_service = WatsonxService()
                        result = watsonx_service.chat_response(prompt)
                        
                        if result['status'] == 'success':
                            response = result['response']
                            st.markdown(response)
                            st.caption("⚠️ General response - Upload a document for context-aware answers")
                        else:
                            error_msg = f"❌ Error: {result['error']}"
                            st.error(error_msg)
                            response = error_msg
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"❌ Unexpected error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History", key="clear_chat"):
        st.session_state.messages = []
        document_service.clear_documents()
        st.rerun()

def call_data_analysis():
    """Handle call data analysis functionality."""
    st.header("📊 TRAI Telecom Compliance Analysis")
    
    # Initialize services
    if "document_service" not in st.session_state:
        st.session_state.document_service = DocumentService()
    document_service = st.session_state.document_service
    call_data_service = CallDataService()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Regulatory document upload
        st.subheader("📜 Upload TRAI Regulatory Document")
        reg_file = st.file_uploader(
            "Upload TRAI regulations for compliance context",
            type=['pdf', 'docx', 'txt'],
            help="Upload TRAI regulations to enhance compliance analysis accuracy",
            key="trai_reg_file"
        )
        
        if reg_file:
            with st.spinner("🔍 Processing TRAI regulations..."):
                reg_file.seek(0)
                
                try:
                    if reg_file.type == "text/plain":
                        reg_text = str(reg_file.read(), "utf-8")
                    elif reg_file.type == "application/pdf":
                        import pypdf
                        reader = pypdf.PdfReader(reg_file)
                        reg_text = "\n".join([page.extract_text() for page in reader.pages])
                    elif reg_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        from docx import Document
                        doc = Document(reg_file)
                        reg_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                    
                    if reg_text.strip():
                        result = document_service.add_document(reg_text, reg_file.name)
                        if result["success"]:
                            if result.get('will_use_summary', False):
                                st.success("✅ TRAI regulatory document processed! Large document will be summarized for compliance analysis.")
                            else:
                                st.success("✅ TRAI regulatory document processed! Full document will be used for enhanced compliance analysis.")
                        else:
                            st.error(f"❌ Processing failed: {result['error']}")
                    else:
                        st.warning("⚠️ Document appears to be empty")
                    
                except Exception as e:
                    st.error(f"❌ Error processing regulatory document: {str(e)}")
    
    with col2:
        if document_service.has_documents():
            st.success("📜 TRAI Context: Active")
        else:
            st.info("📜 Upload TRAI regulations for enhanced analysis")
    
    st.markdown("---")
    
    # Call data upload and analysis
    st.subheader("📊 Upload Call Data for Compliance Analysis")
    
    call_data_file = st.file_uploader(
        "Upload Excel file with call data",
        type=['xlsx'],
        help="Excel file should contain columns: customer_id, service_area, tot_call_cnt_d, call_drop_cnt_d",
        key="call_data_file"
    )
    
    if call_data_file:
        with st.spinner("📊 Analyzing call data for TRAI compliance..."):
            try:
                # Read Excel file
                df = pd.read_excel(call_data_file)
                
                st.subheader("🔍 Data Overview")
                
                # Display data metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Records", f"{len(df):,}")
                
                with col2:
                    unique_customers = df['customer_id'].nunique() if 'customer_id' in df.columns else 0
                    st.metric("Unique Customers", f"{unique_customers:,}")
                
                with col3:
                    unique_areas = df['service_area'].nunique() if 'service_area' in df.columns else 0
                    st.metric("Service Areas", unique_areas)
                
                with col4:
                    total_calls = df['tot_call_cnt_d'].sum() if 'tot_call_cnt_d' in df.columns else 0
                    st.metric("Total Calls", f"{total_calls:,}")
                
                # Perform compliance analysis
                st.subheader("📋 TRAI Compliance Analysis")
                
                with st.spinner("🧠 Running IBM watsonx.ai compliance analysis..."):
                    analysis_result = call_data_service.analyze_compliance_violations(df)
                
                if analysis_result['success']:
                    violations = analysis_result['violations']
                    
                    # Display violations summary
                    if violations['high_risk']:
                        st.error(f"🚨 **High Risk Violations**: {len(violations['high_risk'])} found")
                        for violation in violations['high_risk'][:3]:  # Show top 3
                            st.write(f"• **{violation['type']}**: {violation['description']}")
                    
                    if violations['medium_risk']:
                        st.warning(f"⚠️ **Medium Risk Issues**: {len(violations['medium_risk'])} found")
                        for violation in violations['medium_risk'][:2]:  # Show top 2
                            st.write(f"• **{violation['type']}**: {violation['description']}")
                    
                    if violations['low_risk']:
                        st.info(f"ℹ️ **Low Risk Items**: {len(violations['low_risk'])} found")
                    
                    # Enhanced analysis with regulatory context
                    if document_service.has_documents():
                        st.subheader("🏛️ Regulatory Context Analysis")
                        with st.spinner("Analyzing with TRAI regulatory context..."):
                            try:
                                context = document_service.get_context_for_query("telecommunications penalties violations fines compliance")
                                watsonx_service = WatsonxService()
                                
                                # Generate prompt using the service method
                                enhanced_prompt = call_data_service.generate_analysis_prompt(violations, context)
                                enhanced_result = watsonx_service.chat_response(enhanced_prompt, context)
                                
                                if enhanced_result['status'] == 'success':
                                    st.write(enhanced_result['response'])
                                    st.caption("🔍 Analysis enhanced with TRAI regulatory context")
                                
                            except Exception as e:
                                st.warning(f"Enhanced analysis unavailable: {str(e)}")
                    
                    # Display data sample
                    st.subheader("📋 Data Sample")
                    st.dataframe(df.head(10), use_container_width=True)
                    
                else:
                    st.error(f"❌ Analysis Failed: {analysis_result['error']}")
                    
            except Exception as e:
                st.error(f"❌ Data Processing Error: {str(e)}")

def main():
    """Main application."""
    setup_page()
    
    # Two-frame layout: left dropdown, right content
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Light background styling for left frame
        st.markdown("""
        <style>
        .stColumn:first-child > div {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #e9ecef;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.subheader("🎯 Use Cases")
        use_case = st.selectbox(
            "Select a use case:",
            ["📊 Document Analysis", "💬 Legal Assistant", "📈 TRAI Compliance"],
            index=0
        )
        
        st.markdown("---")
        
        # Configuration display
        st.subheader("⚙️ Configuration")
        model_id = os.getenv('MODEL_ID', 'meta-llama/llama-3-3-70b-instruct')
        st.info(f"🤖 **LLM Model**\n{model_id}")
        st.info(f"🔗 **watsonx.ai URL**\n{os.getenv('WATSONX_URL', 'Not configured')}")
    
    with col2:
        if use_case == "📊 Document Analysis":
            document_upload_section()
        elif use_case == "💬 Legal Assistant":
            chat_with_documents()
        else:  # TRAI Compliance
            call_data_analysis()
    
    # Footer
    st.markdown("---")
    st.markdown("<p style='text-align: center;'><strong>Built for Red Hat Hackathon 2025</strong></p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Powered by <strong>IBM watsonx.ai and Red Hat Openshift</strong></p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
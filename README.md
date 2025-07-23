# 🧠 LegalTech AI - Red Hat Hackathon

[![OpenShift](https://img.shields.io/badge/OpenShift-Ready-red?style=flat-square&logo=redhat)](https://www.redhat.com/en/technologies/cloud-computing/openshift)
[![IBM watsonx.ai](https://img.shields.io/badge/IBM-watsonx.ai-blue?style=flat-square&logo=ibm)](https://www.ibm.com/watsonx)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-red?style=flat-square&logo=streamlit)](https://streamlit.io)
[![TRAI](https://img.shields.io/badge/TRAI-Compliant-orange?style=flat-square)](https://trai.gov.in)

A comprehensive LegalTech AI application designed for the Red Hat Hackathon, featuring document analysis, RAG-powered chat, and **TRAI telecom compliance analysis**. Built with IBM watsonx.ai and optimized for OpenShift deployment.

## ✨ Key Features

### 📄 Document Analysis
- **Multi-format Support**: PDF, DOCX, TXT file processing
- **AI-Powered Analysis**: Compliance checking and legal summarization
- **Smart Text Extraction**: Handles complex document structures

### 💬 RAG-Powered Chat Assistant  
- **Vector Database**: ChromaDB for efficient document retrieval
- **Semantic Search**: Context-aware responses using sentence transformers
- **Document Context**: Upload regulations for precise legal guidance
- **Chunked Processing**: Handles large documents without token limits

### 📊 TRAI Telecom Compliance Analysis
- **Call Data Processing**: Excel (.xlsx) file analysis with 10,000+ records
- **TRAI 2024 Standards**: Real penalty calculations based on current regulations
- **Multi-Level Detection**: Service area, customer, and overall compliance
- **Call Drop Analysis**: Specialized detection for India's #1 telecom violation
- **Penalty Estimation**: Accurate INR penalty ranges (₹50,000 - ₹10 lakh)

### 🏗️ Production Architecture
- **Microservices Design**: Modular, scalable components
- **OpenShift Ready**: Complete Kubernetes deployment manifests
- **Security First**: Red Hat UBI containers, non-root execution
- **Health Monitoring**: Comprehensive observability

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- IBM watsonx.ai API credentials
- ChromaDB and sentence-transformers (for RAG)

### Local Development

1. **Clone and Install**:
   ```bash
   git clone <repository-url>
   cd legaltech_ai
   pip install -r requirements-simple.txt
   ```

2. **Configure Environment**:
   ```bash
   # Create .env file with your credentials
   cat > .env << EOF
   WATSONX_API_KEY=your_api_key_here
   WATSONX_URL=https://us-south.ml.cloud.ibm.com
   WATSONX_PROJECT_ID=your_project_id_here
   MODEL_ID=meta-llama/llama-3-3-70b-instruct
   PORT=8080
   EOF
   ```

3. **Run Application**:
   ```bash
   python src/legaltech_ai/main.py
   # Access at http://localhost:8080
   ```

## 📖 Usage Guide

### 1. Document Analysis Mode
- Upload PDF/DOCX/TXT legal documents
- Get AI-powered compliance analysis and summaries
- View detailed reports with legal insights

### 2. RAG Chat Assistant
- Upload regulatory documents (e.g., Telecommunications Act 2023)
- Ask questions and get context-aware answers
- Documents are automatically chunked and vectorized
- Semantic search finds relevant sections for responses

### 3. Call Data Analysis Mode
- Upload Excel files with telecom call data
- **TRAI Compliance Checking**: Automated violation detection
- **Penalty Calculations**: Real INR amounts based on 2024 regulations
- **Service Area Analysis**: Geographic compliance mapping
- **Customer Impact**: Individual drop rate analysis

#### Sample Excel Format:
```
customer_id | service_area | tot_call_cnt_d | call_drop_cnt_d
9966767161  | Maharashtra  | 17             | 0
9966767162  | Mumbai       | 20             | 0  
9966767165  | North East   | 17             | 5
```

## 🎯 TRAI Compliance Features

### Call Drop Analysis
- **2% Benchmark**: TRAI's maximum allowed call drop rate
- **Service Area Detection**: Identifies areas exceeding limits
- **Penalty Tiers**: ₹50,000 to ₹10 lakh based on violation severity
- **Customer Impact**: Individual high-drop-rate analysis

### Violation Categories
- **High Risk**: Direct TRAI limit violations (₹1-10 lakh penalties)
- **Medium Risk**: Warning levels and monitoring required
- **Low Risk**: Data quality and minor compliance issues

### AI Analysis
- **Regulatory Context**: Uses uploaded TRAI documents
- **Specific Penalties**: Real INR amounts per violation type
- **Actionable Recommendations**: Immediate steps to fix issues
- **Legal References**: TRAI regulation citations

## 🔧 Technology Stack

### Core Technologies
- **Python 3.11+**: Modern Python with async support
- **Streamlit**: Interactive web interface
- **IBM watsonx.ai**: Large language model integration
- **ChromaDB**: Vector database for RAG
- **sentence-transformers**: Text embeddings (all-MiniLM-L6-v2)
- **pandas + openpyxl**: Excel data processing

### AI & ML Pipeline
```
Document Upload → Text Extraction → Chunking → Vectorization → ChromaDB Storage
                                                                      ↓
User Query → Vector Search → Context Retrieval → watsonx.ai → Response
```

### Deployment Stack
- **Red Hat OpenShift**: Container orchestration
- **Red Hat UBI**: Secure base containers
- **Kubernetes**: Auto-scaling and health monitoring
- **Docker**: Containerization

## 📁 Project Structure

```
src/legaltech_ai/
├── main.py                 # Application entry point
├── watsonx_service.py      # IBM watsonx.ai integration
├── rag_service.py          # ChromaDB RAG implementation
├── call_data_service.py    # TRAI compliance analysis
└── ui/
    └── streamlit_app.py    # Multi-mode Streamlit interface

requirements-simple.txt     # Python dependencies
Dockerfile                 # Container definition
.env                       # Environment configuration
data.xlsx                  # Sample telecom data (10,000 records)
```

## 🛡️ Security & Compliance

### Container Security
- **Red Hat UBI9**: Enterprise-grade base image
- **Non-root Execution**: Enhanced security posture
- **Resource Limits**: CPU/memory constraints
- **Health Checks**: Kubernetes-native monitoring

### Data Security
- **Environment Variables**: Secure credential management
- **Input Validation**: File size and type restrictions
- **Error Handling**: No sensitive data in logs

## 🚀 OpenShift Deployment

### Prerequisites
- OpenShift CLI (`oc`) installed and configured
- Docker/Podman for container builds
- Access to OpenShift cluster with project creation permissions

### Simple One-Command Deployment

1. **Build and push container image**:
   ```bash
   # Build locally or use OpenShift BuildConfig
   docker build -t legaltech-ai:latest .
   docker tag legaltech-ai:latest your-registry/legaltech-ai:latest
   docker push your-registry/legaltech-ai:latest
   ```

2. **Deploy everything with single file**:
   ```bash
   # Create project
   oc new-project legaltech-ai
   
   # Deploy all resources (ConfigMap, Secret, Deployment, Service, Route)
   oc apply -f openshift-deployment.yaml
   ```

3. **Verify deployment**:
   ```bash
   oc get pods -l app=legaltech-ai
   oc get route legaltech-ai-route
   ```

### Alternative: OpenShift Source-to-Image (S2I)

For direct source deployment without pre-built images:
```bash
oc new-project legaltech-ai
oc new-app python:3.11~https://github.com/your-repo/legaltech-ai.git \
  --name=legaltech-ai \
  --env WATSONX_API_KEY="your_api_key" \
  --env WATSONX_URL="https://us-south.ml.cloud.ibm.com" \
  --env WATSONX_PROJECT_ID="your_project_id"
oc expose service/legaltech-ai
```

### Post-Deployment Verification

1. **Check application health**:
   ```bash
   # Get application URL
   ROUTE_HOST=$(oc get route legaltech-ai-route -o jsonpath='{.spec.host}')
   curl -f https://$ROUTE_HOST
   ```

2. **View application logs**:
   ```bash
   oc logs -f deployment/legaltech-ai
   ```

3. **Access features**:
   - **Main App**: `https://your-route-host`
   - **Document Analysis**: Upload PDF/DOCX/TXT files
   - **RAG Chat**: Upload regulations and ask questions
   - **TRAI Analysis**: Upload Excel call data files

### Configuration Management

The `openshift-deployment.yaml` includes:
- **ConfigMap**: Non-sensitive configuration (URLs, model settings)
- **Secret**: Sensitive credentials (API keys)  
- **Deployment**: Application with health checks and resource limits
- **Service**: Internal cluster networking
- **Route**: External HTTPS access with SSL termination

### Scaling and Management

1. **Scale application**:
   ```bash
   oc scale deployment/legaltech-ai --replicas=3
   ```

2. **Update configuration**:
   ```bash
   # Edit the deployment file and reapply
   oc apply -f openshift-deployment.yaml
   ```

3. **View resource usage**:
   ```bash
   oc top pods -l app=legaltech-ai
   ```

### Troubleshooting

1. **Pod not starting**:
   ```bash
   oc describe pod -l app=legaltech-ai
   oc logs -l app=legaltech-ai --previous
   ```

2. **Route issues**:
   ```bash
   oc describe route legaltech-ai-route
   ```

## 📊 Performance & Monitoring

### RAG Performance
- **ChromaDB**: In-memory vector storage for fast retrieval
- **Chunking**: 1000-character chunks with 200-character overlap
- **Search**: Top-3 relevant chunks per query
- **Context Limit**: 4000 characters to stay within token limits

### Call Data Processing
- **Large Dataset Support**: Handles 10,000+ records efficiently
- **Real-time Analysis**: Sub-second violation detection
- **Memory Optimization**: Pandas vectorized operations

## 🏆 Red Hat Hackathon Highlights

### Innovation
- **TRAI Compliance AI**: First-of-its-kind automated telecom compliance
- **RAG Integration**: Advanced retrieval-augmented generation
- **Multi-modal Analysis**: Documents + structured data + chat

### Production Readiness
- **Enterprise Architecture**: Microservices with proper separation
- **OpenShift Native**: Complete Kubernetes deployment
- **Security Best Practices**: Non-root containers, secret management
- **Observability**: Health checks, logging, monitoring

### Business Impact
- **Cost Savings**: Automated compliance reduces manual review
- **Risk Mitigation**: Early violation detection prevents penalties
- **Regulatory Alignment**: Real TRAI 2024 standards implementation

## 🔍 Sample Use Cases

### Telecom Operator Compliance
1. Upload daily call data Excel files
2. Get instant TRAI compliance report
3. Identify service areas needing attention
4. Receive penalty estimates and mitigation steps

### Legal Document Review
1. Upload Telecommunications Act 2023
2. Ask questions about specific regulations
3. Get contextual answers with legal citations
4. Export compliance reports

### Regulatory Research
1. Upload multiple regulatory documents
2. Chat with the knowledge base
3. Get comparative analysis across regulations
4. Generate compliance checklists

## 📜 License

MIT License - Built for Red Hat Hackathon

## 🤝 Acknowledgments

- **Red Hat OpenShift**: Cloud-native platform
- **IBM watsonx.ai**: Advanced AI capabilities  
- **TRAI**: Telecommunications regulatory framework
- **Open Source Community**: ChromaDB, Streamlit, sentence-transformers

---

**Built with ❤️ for the Red Hat Hackathon**  
*Demonstrating enterprise AI, regulatory compliance, and cloud-native architecture*
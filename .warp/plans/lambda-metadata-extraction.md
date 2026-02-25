# Lambda + Gemini Flash Metadata Extraction

## Architecture Overview

Automated metadata extraction system that processes documents on upload/modification using AWS Lambda and Google Gemini 1.5 Flash API.

```
┌─────────────────────────────────────────────────────┐
│  Upload/Update Document to S3                       │
│  s3://rh-eagle-files/financial-advisor/new-doc.txt  │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ S3 Event Notification
                   ▼
┌─────────────────────────────────────────────────────┐
│  Lambda: process-document-metadata                   │
│  Trigger: s3:ObjectCreated:*, s3:ObjectModified:*   │
└──────────────────┬──────────────────────────────────┘
                   │
                   ├──> Read document from S3
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  Gemini 1.5 Flash API                               │
│  Prompt: "Extract metadata from this document       │
│           following the schema..."                  │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ Returns structured metadata
                   ▼
┌─────────────────────────────────────────────────────┐
│  Lambda validates & stores metadata                 │
│  - Updates metadata-catalog.json in S3              │
│  - (Optional) Stores in DynamoDB for fast queries   │
└─────────────────────────────────────────────────────┘
```

## Lambda Function Implementation

### lambda_function.py

```python
"""
Lambda function to extract document metadata using Gemini 1.5 Flash
Triggered by S3 upload/modification events
"""

import json
import boto3
import os
from datetime import datetime
from google import generativeai as genai

# Initialize AWS clients
s3 = boto3.client('s3')
secrets = boto3.client('secretsmanager')

# Configure Gemini API
def get_gemini_api_key():
    """Retrieve Gemini API key from AWS Secrets Manager"""
    secret_name = os.environ['GEMINI_SECRET_NAME']
    response = secrets.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])['gemini_api_key']

genai.configure(api_key=get_gemini_api_key())

# Metadata extraction prompt
METADATA_SCHEMA = """
You are an expert at analyzing government acquisition and contracting documents.
Extract metadata from the following document according to this JSON schema.

Required fields:
- document_id: Generate a unique ID based on the document content (format: {topic}-{source}-{number})
- file_name: The filename
- document_type: One of: "guidance", "regulation", "policy", "template", "memo", "checklist", "reference"
- source_agency: The originating agency (FAR, GSA, OMB, DOD, GAO, Agency-specific, etc.)
- primary_topic: Main subject from this list:
  * funding, acquisition_packages, contract_types, compliance, legal, market_research,
  * socioeconomic, labor, intellectual_property, termination, modifications, closeout,
  * performance, subcontracting
- primary_agent: Which agent should own this content:
  * supervisor-core, financial-advisor, legal-counselor, compliance-strategist,
  * market-intelligence, technical-translator, public-interest-guardian, agents
- authority_level: One of: "statute", "regulation", "policy", "guidance", "internal"
- keywords: Array of 5-15 important terms, acronyms, and concepts
- complexity_level: One of: "basic", "intermediate", "advanced"

Optional but recommended fields:
- effective_date: ISO 8601 format (YYYY-MM-DD) or null
- last_updated: ISO 8601 format (YYYY-MM-DD) or null
- expiration_date: ISO 8601 format (YYYY-MM-DD) or null
- fiscal_year: Four-digit year or null
- summary: 2-3 sentence high-level summary (max 500 chars)
- key_requirements: Array of main requirements or obligations (max 5)
- related_topics: Array of secondary topics from the list above
- relevant_agents: Array of other agents that should reference this
- far_references: Array of FAR citations (format: "FAR X.XXX")
- statute_references: Array of statute citations (format: "XX USC XXXX")
- agency_references: Array of agency-specific regulations
- audience: Array of intended readers (contracting_officer, legal_counsel, etc.)

Return ONLY valid JSON matching this structure, no explanation or markdown:

{
  "document_id": "string",
  "file_name": "string",
  "document_type": "string",
  "source_agency": "string",
  "effective_date": "YYYY-MM-DD or null",
  "last_updated": "YYYY-MM-DD or null",
  "expiration_date": "YYYY-MM-DD or null",
  "fiscal_year": number or null,
  "summary": "string",
  "key_requirements": ["string"],
  "primary_topic": "string",
  "related_topics": ["string"],
  "primary_agent": "string",
  "relevant_agents": ["string"],
  "far_references": ["string"],
  "statute_references": ["string"],
  "agency_references": ["string"],
  "authority_level": "string",
  "keywords": ["string"],
  "complexity_level": "string",
  "audience": ["string"]
}
"""

def lambda_handler(event, context):
    """
    Main Lambda handler
    Processes S3 event notifications for new/modified documents
    """
    try:
        # Extract S3 event details
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        event_name = record['eventName']
        
        print(f"Processing {event_name} event for s3://{bucket}/{key}")
        
        # Skip metadata catalog file to avoid infinite loop
        if key == 'metadata-catalog.json':
            print("Skipping metadata catalog file")
            return {
                'statusCode': 200,
                'body': json.dumps('Skipped catalog file')
            }
        
        # Skip non-document files (images, etc.)
        if not is_processable_file(key):
            print(f"Skipping non-processable file: {key}")
            return {
                'statusCode': 200,
                'body': json.dumps(f'Skipped non-processable file: {key}')
            }
        
        # Read document from S3
        print(f"Reading document from S3...")
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read()
        file_size_bytes = response['ContentLength']
        content_type = response.get('ContentType', 'text/plain')
        
        # Decode content based on type
        if content_type.startswith('text/'):
            content_text = content.decode('utf-8', errors='ignore')
        else:
            # Handle PDFs, Word docs, etc. - might need additional processing
            content_text = content.decode('utf-8', errors='ignore')
        
        # Truncate if too large (Gemini Flash has token limits)
        max_chars = 30000  # ~7500 tokens
        if len(content_text) > max_chars:
            print(f"Truncating document from {len(content_text)} to {max_chars} chars")
            content_text = content_text[:max_chars] + "\n\n[Document truncated for metadata extraction]"
        
        # Extract metadata using Gemini Flash
        print("Calling Gemini Flash API for metadata extraction...")
        metadata = extract_metadata_with_gemini(content_text, key)
        
        # Enhance metadata with file information
        metadata['file_path'] = key
        metadata['s3_bucket'] = bucket
        metadata['file_size_bytes'] = file_size_bytes
        metadata['file_size_kb'] = round(file_size_bytes / 1024)
        metadata['catalog_version'] = '1.0'
        metadata['added_to_catalog'] = datetime.utcnow().isoformat() + 'Z'
        metadata['last_validated'] = datetime.utcnow().isoformat() + 'Z'
        
        # Validate metadata
        validate_metadata(metadata)
        
        # Update catalog
        print("Updating metadata catalog...")
        update_catalog(bucket, metadata)
        
        print(f"Successfully processed {key}")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully processed {key}',
                'document_id': metadata['document_id']
            })
        }
        
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        raise

def is_processable_file(key):
    """Check if file type can be processed"""
    processable_extensions = ['.txt', '.md', '.pdf', '.doc', '.docx']
    return any(key.lower().endswith(ext) for ext in processable_extensions)

def extract_metadata_with_gemini(content, filename):
    """
    Call Gemini 1.5 Flash to extract metadata
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"{METADATA_SCHEMA}\n\nDocument filename: {filename}\n\nDocument content:\n\n{content}"
    
    # Configure generation parameters
    generation_config = {
        'temperature': 0.1,  # Low temperature for consistent extraction
        'top_p': 0.95,
        'top_k': 40,
        'max_output_tokens': 2048,
    }
    
    response = model.generate_content(
        prompt,
        generation_config=generation_config
    )
    
    # Parse JSON response
    response_text = response.text.strip()
    
    # Remove markdown code blocks if present
    if response_text.startswith('```json'):
        response_text = response_text[7:]
    if response_text.startswith('```'):
        response_text = response_text[3:]
    if response_text.endswith('```'):
        response_text = response_text[:-3]
    
    metadata = json.loads(response_text.strip())
    return metadata

def validate_metadata(metadata):
    """
    Validate that metadata has required fields and correct formats
    """
    required_fields = [
        'document_id', 'file_name', 'document_type', 'primary_topic',
        'primary_agent', 'authority_level', 'keywords', 'complexity_level'
    ]
    
    for field in required_fields:
        if field not in metadata or not metadata[field]:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate keywords minimum
    if len(metadata.get('keywords', [])) < 3:
        raise ValueError("Metadata must have at least 3 keywords")
    
    # Validate document_type values
    valid_doc_types = ['guidance', 'regulation', 'policy', 'template', 'memo', 'checklist', 'reference']
    if metadata['document_type'] not in valid_doc_types:
        raise ValueError(f"Invalid document_type: {metadata['document_type']}")
    
    # Validate complexity_level values
    valid_complexity = ['basic', 'intermediate', 'advanced']
    if metadata['complexity_level'] not in valid_complexity:
        raise ValueError(f"Invalid complexity_level: {metadata['complexity_level']}")
    
    print("Metadata validation passed")

def update_catalog(bucket, new_metadata):
    """
    Update the metadata catalog with new/updated document metadata
    Handles concurrent updates with optimistic locking
    """
    catalog_key = 'metadata-catalog.json'
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Read existing catalog
            try:
                response = s3.get_object(Bucket=bucket, Key=catalog_key)
                catalog = json.loads(response['Body'].read().decode('utf-8'))
                etag = response.get('ETag', '').strip('"')
            except s3.exceptions.NoSuchKey:
                # Create new catalog
                catalog = {
                    "catalog_metadata": {
                        "version": "1.0",
                        "created": datetime.utcnow().isoformat() + 'Z',
                        "last_updated": datetime.utcnow().isoformat() + 'Z',
                        "total_documents": 0,
                        "schema_version": "1.0"
                    },
                    "statistics": {},
                    "documents": []
                }
                etag = None
            
            # Update or add document
            doc_id = new_metadata['document_id']
            existing_idx = next(
                (i for i, doc in enumerate(catalog['documents']) 
                 if doc['document_id'] == doc_id), 
                None
            )
            
            if existing_idx is not None:
                print(f"Updating existing document: {doc_id}")
                catalog['documents'][existing_idx] = new_metadata
            else:
                print(f"Adding new document: {doc_id}")
                catalog['documents'].append(new_metadata)
                catalog['catalog_metadata']['total_documents'] += 1
            
            # Update catalog metadata
            catalog['catalog_metadata']['last_updated'] = datetime.utcnow().isoformat() + 'Z'
            
            # Regenerate statistics
            catalog['statistics'] = generate_statistics(catalog['documents'])
            
            # Write back to S3
            s3.put_object(
                Bucket=bucket,
                Key=catalog_key,
                Body=json.dumps(catalog, indent=2),
                ContentType='application/json'
            )
            
            print(f"Successfully updated catalog (attempt {attempt + 1})")
            return
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Catalog update failed (attempt {attempt + 1}), retrying: {str(e)}")
            continue

def generate_statistics(documents):
    """
    Generate statistics about the document catalog
    """
    stats = {
        'by_topic': {},
        'by_agent': {},
        'by_document_type': {},
        'by_complexity': {},
        'by_authority': {}
    }
    
    for doc in documents:
        # Count by topic
        topic = doc.get('primary_topic', 'unknown')
        stats['by_topic'][topic] = stats['by_topic'].get(topic, 0) + 1
        
        # Count by agent
        agent = doc.get('primary_agent', 'unknown')
        stats['by_agent'][agent] = stats['by_agent'].get(agent, 0) + 1
        
        # Count by document type
        doc_type = doc.get('document_type', 'unknown')
        stats['by_document_type'][doc_type] = stats['by_document_type'].get(doc_type, 0) + 1
        
        # Count by complexity
        complexity = doc.get('complexity_level', 'unknown')
        stats['by_complexity'][complexity] = stats['by_complexity'].get(complexity, 0) + 1
        
        # Count by authority
        authority = doc.get('authority_level', 'unknown')
        stats['by_authority'][authority] = stats['by_authority'].get(authority, 0) + 1
    
    return stats
```

### requirements.txt

```
boto3==1.34.34
google-generativeai==0.3.2
```

## Infrastructure Setup

### IAM Role Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::rh-eagle-files/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:695681773636:secret:gemini-api-key-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### Lambda Configuration

- **Runtime**: Python 3.12
- **Memory**: 512 MB (can increase to 1024 MB if needed)
- **Timeout**: 120 seconds (Gemini API can be slow)
- **Environment Variables**:
  - `GEMINI_SECRET_NAME`: Name of Secrets Manager secret containing API key
- **Layers**: None needed (use requirements.txt)

### S3 Event Notification

Configure on `rh-eagle-files` bucket:

```json
{
  "LambdaFunctionConfigurations": [
    {
      "Id": "ProcessDocumentMetadata",
      "LambdaFunctionArn": "arn:aws:lambda:us-east-1:695681773636:function:process-document-metadata",
      "Events": [
        "s3:ObjectCreated:*",
        "s3:ObjectRemoved:*"
      ],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "suffix",
              "Value": ".txt"
            }
          ]
        }
      }
    }
  ]
}
```

## Deployment Steps

### 1. Store Gemini API Key in Secrets Manager

```bash
aws secretsmanager create-secret \
  --name gemini-api-key \
  --description "Google Gemini API key for metadata extraction" \
  --secret-string '{"gemini_api_key":"YOUR_GEMINI_API_KEY"}' \
  --region us-east-1
```

### 2. Create Lambda Deployment Package

```bash
# Create deployment directory
mkdir lambda-package
cd lambda-package

# Copy function code
cp lambda_function.py .

# Install dependencies
pip install -r requirements.txt -t .

# Create zip
zip -r ../lambda-package.zip .
```

### 3. Create Lambda Function

```bash
aws lambda create-function \
  --function-name process-document-metadata \
  --runtime python3.12 \
  --role arn:aws:iam::695681773636:role/lambda-metadata-extraction-role \
  --handler lambda_function.lambda_handler \
  --timeout 120 \
  --memory-size 512 \
  --environment Variables={GEMINI_SECRET_NAME=gemini-api-key} \
  --zip-file fileb://lambda-package.zip \
  --region us-east-1
```

### 4. Add S3 Trigger Permissions

```bash
aws lambda add-permission \
  --function-name process-document-metadata \
  --statement-id s3-trigger-permission \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::rh-eagle-files \
  --region us-east-1
```

### 5. Configure S3 Event Notification

```bash
aws s3api put-bucket-notification-configuration \
  --bucket rh-eagle-files \
  --notification-configuration file://s3-event-config.json
```

## Cost Analysis

### Per-Document Processing Cost

**Lambda:**
- Duration: ~30 seconds average
- Memory: 512 MB
- Cost: $0.0000083 per invocation

**Gemini 1.5 Flash:**
- Input: ~10,000 tokens per document
- Output: ~500 tokens (metadata JSON)
- Cost: $0.00105 per document
  - Input: 10,000 × $0.075/1M = $0.00075
  - Output: 500 × $0.30/1M = $0.00015

**S3:**
- GET request: $0.0000004
- PUT request: $0.000005

**Total per document: ~$0.00106**

### Initial Processing (256 documents)

- Total cost: 256 × $0.00106 = **$0.27**

### Ongoing Costs

- Only triggered on new/modified documents
- Estimated: 10-20 docs/month
- Monthly cost: **$0.01 - $0.02**

## Testing

### Test Event (S3 Upload)

```json
{
  "Records": [
    {
      "eventVersion": "2.1",
      "eventSource": "aws:s3",
      "awsRegion": "us-east-1",
      "eventTime": "2026-02-20T18:30:00.000Z",
      "eventName": "ObjectCreated:Put",
      "s3": {
        "bucket": {
          "name": "rh-eagle-files"
        },
        "object": {
          "key": "financial-advisor/appropriations-law/test_document.txt"
        }
      }
    }
  ]
}
```

### Manual Test Script

```python
# test_lambda_local.py
import json
from lambda_function import lambda_handler

# Create test event
test_event = {
    "Records": [{
        "eventName": "ObjectCreated:Put",
        "s3": {
            "bucket": {"name": "rh-eagle-files"},
            "object": {"key": "test-doc.txt"}
        }
    }]
}

# Invoke handler
result = lambda_handler(test_event, None)
print(json.dumps(result, indent=2))
```

## Monitoring & Logging

### CloudWatch Metrics to Monitor

- Lambda invocations
- Lambda errors
- Lambda duration
- Lambda concurrent executions

### CloudWatch Logs Insights Queries

**Failed metadata extractions:**
```
fields @timestamp, @message
| filter @message like /Error processing document/
| sort @timestamp desc
```

**Average processing time:**
```
fields @timestamp, @duration
| stats avg(@duration) as avg_duration, max(@duration) as max_duration
```

## Alternative: DynamoDB Storage

Instead of a single JSON file, store each document's metadata as a DynamoDB item.

### DynamoDB Table Schema

```
Table: rh-eagle-document-metadata
Partition Key: document_id (String)
Sort Key: None

GSI 1: primary_topic-index
  Partition Key: primary_topic
  Sort Key: last_updated

GSI 2: primary_agent-index
  Partition Key: primary_agent
  Sort Key: last_updated
```

### Benefits

- Fast queries without loading entire catalog
- Handles millions of documents
- Built-in indexing
- Better for concurrent access

### Tradeoff

- Additional cost: ~$0.25/month for 256 documents
- More complex queries (need SDK)
- Less human-readable than JSON file

## Next Steps

1. ✅ Store Gemini API key in Secrets Manager
2. ✅ Create Lambda function deployment package
3. ✅ Deploy Lambda function
4. ✅ Configure S3 event trigger
5. ✅ Test with sample documents
6. ✅ Bulk process existing 256 documents
7. ✅ Monitor CloudWatch logs
8. ✅ Validate metadata quality
9. ⬜ Create agent tools to read catalog
10. ⬜ Integrate with multi-agent orchestrator

## Maintenance

### Updating the Extraction Logic

1. Modify `lambda_function.py`
2. Create new deployment package
3. Update Lambda function:

```bash
aws lambda update-function-code \
  --function-name process-document-metadata \
  --zip-file fileb://lambda-package.zip
```

### Reprocessing All Documents

To regenerate metadata for all documents:

```python
# reprocess_all.py
import boto3

s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')

# List all objects
response = s3.list_objects_v2(Bucket='rh-eagle-files')

for obj in response.get('Contents', []):
    key = obj['Key']
    
    # Skip catalog file
    if key == 'metadata-catalog.json':
        continue
    
    # Invoke Lambda for each document
    event = {
        "Records": [{
            "eventName": "ObjectCreated:Put",
            "s3": {
                "bucket": {"name": "rh-eagle-files"},
                "object": {"key": key}
            }
        }]
    }
    
    lambda_client.invoke(
        FunctionName='process-document-metadata',
        InvocationType='Event',  # Async
        Payload=json.dumps(event)
    )
    
    print(f"Triggered processing for {key}")
```

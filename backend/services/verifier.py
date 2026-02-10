"""
Skills grounding verifier (Q3).
Ensures AI-generated drafts only mention skills the user actually has.
"""
import re
from typing import List


# Common technical skill patterns to look for in text
SKILL_PATTERN = re.compile(
    r'\b(?:AWS|Azure|GCP|Docker|Kubernetes|K8s|Terraform|Ansible|Jenkins|'
    r'CI/CD|Linux|Python|Java|JavaScript|TypeScript|React|Node\.js|Go|Rust|'
    r'PostgreSQL|MongoDB|Redis|MySQL|Kafka|RabbitMQ|Nginx|Apache|'
    r'Git|GitHub|GitLab|Bitbucket|Jira|Confluence|'
    r'DevOps|SRE|MLOps|DataOps|CloudOps|NetOps|'
    r'Prometheus|Grafana|Datadog|Splunk|ELK|'
    r'HTML|CSS|Vue|Angular|Django|Flask|FastAPI|Spring|'
    r'S3|EC2|Lambda|ECS|EKS|RDS|CloudFormation|CDK|'
    r'Helm|ArgoCD|FluxCD|Istio|Envoy|'
    r'TCP/IP|DNS|HTTP|REST|GraphQL|gRPC|WebSocket|'
    r'Bash|Shell|PowerShell|Perl|Ruby|PHP|Scala|Kotlin|Swift|'
    r'TensorFlow|PyTorch|Spark|Hadoop|Airflow|dbt|'
    r'Vagrant|Packer|Consul|Vault|Nomad)\b',
    re.IGNORECASE
)

# H4: Synonym Normalization Map (Canonical form is lowercase)
SYNONYM_MAP = {
    "js": "javascript",
    "ts": "typescript",
    "k8s": "kubernetes",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "reactjs": "react",
    "node": "node.js",
    "nodejs": "node.js",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "react.js": "react",
    "golang": "go",
}

def normalize_skill(skill: str) -> str:
    """Normalize skill to canonical form for comparison."""
    s = skill.lower().strip()
    return SYNONYM_MAP.get(s, s)


def extract_skill_mentions(draft_text: str) -> List[str]:
    """Extract all technical skill mentions from draft text."""
    matches = SKILL_PATTERN.findall(draft_text)
    # Normalize and deduplicate
    seen = set()
    unique = []
    for m in matches:
        key = m.lower()
        if key not in seen:
            seen.add(key)
            unique.append(m)
    return unique


def verify_skills_grounding(draft_text: str, user_skills: List[str]) -> dict:
    """Check that all skills mentioned in a draft actually exist in user profile.
    
    Returns:
        dict with 'grounded', 'hallucinated', and 'is_valid' keys.
    """
    mentioned = extract_skill_mentions(draft_text)
    
    # Normalize user skills for comparison
    user_skills_norm = {normalize_skill(s) for s in user_skills}
    
    grounded = []
    hallucinated = []
    
    for skill in mentioned:
        skill_norm = normalize_skill(skill)
        # Check if skill matches any user skill (partial match for compound skills)
        # We check normalized forms
        is_grounded = False
        
        # Direct match check
        if skill_norm in user_skills_norm:
            is_grounded = True
        else:
            # Fuzzy/Substring check on normalized forms
            for us in user_skills_norm:
                if skill_norm in us or us in skill_norm:
                    is_grounded = True
                    break
        
        if is_grounded:
            grounded.append(skill)
        else:
            hallucinated.append(skill)
    
    return {
        "grounded": grounded,
        "hallucinated": hallucinated,
        "is_valid": len(hallucinated) == 0,
        "total_mentioned": len(mentioned),
    }

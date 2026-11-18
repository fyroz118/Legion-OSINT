"""Apply owner-issued channel discovery decisions from GitHub repository_dispatch."""
import json
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
event=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
payload=event.get("client_payload",{})
username=str(payload.get("username","")).strip().lstrip("@")
decision=str(payload.get("decision","")).strip().lower()
if not username or not username.replace("_","").isalnum() or decision not in ("approve","reject"):
    raise SystemExit("Invalid channel decision payload")
seed_path=ROOT/"discovery/seed_candidates.json"
active_path=ROOT/"config/channels.json"
seed=json.loads(seed_path.read_text(encoding="utf-8"))
active=json.loads(active_path.read_text(encoding="utf-8"))
candidate=next((x for x in seed.get("candidates",[]) if x.get("username","").lower()==username.lower()),None)
if candidate is None: raise SystemExit("Candidate not found")
if decision=="approve":
    if not any(x.get("username","").lower()==username.lower() for x in active.get("channels",[])):
        active["channels"].append({
            "username":candidate["username"],"priority":str(candidate.get("region","global")).lower().replace(" ","_"),
            "language":candidate.get("language","und"),"source_type":candidate.get("candidate_category","discovered_public_channel"),
            "source_affiliation":candidate.get("source_affiliation","unverified"),"default_evidence_status":"UNVERIFIED","enabled":True,
            "notes":"Owner-approved discovery candidate. Identity and editorial independence may remain uncertain; posts are UNVERIFIED leads. "+str(candidate.get("discovery_notes","")),
            "source_class":candidate.get("source_class","unknown").replace("_candidate",""),"monitoring_weight":"standard",
            "discovery_source_url":candidate.get("seed_source_url","")})
    candidate["review_status"]="OWNER_APPROVED"
    candidate["enabled_for_collection"]=True
else:
    candidate["review_status"]="OWNER_REJECTED"
    candidate["enabled_for_collection"]=False
seed_path.write_text(json.dumps(seed,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
active_path.write_text(json.dumps(active,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
print("Applied",decision,"for",username)

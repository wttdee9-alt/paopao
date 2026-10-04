import hashlib,requests
class MetaAPIError(RuntimeError):pass
class MetaAdsProvider:
    def __init__(self,token,api_version="v24.0"):self.token=token;self.base=f"https://graph.facebook.com/{api_version}"
    def _get(self,path,p):
        p=dict(p);p["access_token"]=self.token;r=requests.get(f"{self.base}/{path}",params=p,timeout=40)
        if not r.ok:raise MetaAPIError(f"Meta API {r.status_code}: {r.text[:500]}")
        return r.json()
    def list_accounts(self):return self._get("me/adaccounts",{"fields":"id,name,account_id,currency,timezone_name","limit":100}).get("data",[])
    def fetch_insights(self,account,since,until,breakdowns=None):
        p={"level":"ad","fields":"campaign_id,adset_id,ad_id,spend,impressions,clicks,actions,action_values","time_range":f'{{"since":"{since}","until":"{until}"}}',"time_increment":1,"limit":500}
        if breakdowns:p["breakdowns"]=breakdowns
        return self._get(f"act_{account}/insights",p).get("data",[])
def sync_meta_to_db(db,provider,account,since,until):
    fam=[("base",None),("demographic","age,gender"),("region","region"),("delivery","publisher_platform,platform_position,device_platform"),("hourly","hourly_stats_aggregated_by_advertiser_time_zone")];counts={}
    for grain,bd in fam:
        rows=provider.fetch_insights(account,since,until,bd);counts[grain]=len(rows)
        for r in rows:
            actions={x.get("action_type"):float(x.get("value",0) or 0) for x in r.get("actions",[])}
            msgs=int(max(actions.get("onsite_conversion.messaging_conversation_started_7d",0),actions.get("messaging_conversation_started_7d",0)))
            row={"date":r.get("date_start",since),"hour_bucket":r.get("hourly_stats_aggregated_by_advertiser_time_zone"),"campaign_id":r.get("campaign_id"),"adset_id":r.get("adset_id"),"ad_id":r.get("ad_id"),"age":r.get("age"),"gender":r.get("gender"),"region":r.get("region"),"publisher_platform":r.get("publisher_platform"),"platform_position":r.get("platform_position"),"device_platform":r.get("device_platform"),"spend":float(r.get("spend",0) or 0),"impressions":int(float(r.get("impressions",0) or 0)),"clicks":int(float(r.get("clicks",0) or 0)),"messaging_conversations":msgs,"purchases":0,"purchase_value":0,"source_grain":grain}
            row["source_key"]=hashlib.sha256(repr(sorted(row.items())).encode()).hexdigest();db.insert_insight(row)
    return counts

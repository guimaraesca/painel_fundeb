#!/usr/bin/env python3
"""
Consolida os dados processados (data/processed/*.json) no payload único
que alimenta o painel (data/processed/payload.json).

Entra: base_clean.json (FNDE Fundeb 2026), v2025.json (VAAR 2025),
ideb.json, rend.json, inse.json, conect.json, sim_atend.json (matrículas históricas e IEE/IAE).
Sai:   payload.json  (cols, rows, pend, nat, byuf, bncc)

Uso:   python src/build_payload.py
Não requer dependências externas (apenas biblioteca padrão).
"""
import json, pathlib
from collections import defaultdict, Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"

def load(name):
    p = PROC / name
    return json.load(open(p, encoding="utf-8")) if p.exists() else {}

SIG2COD = {'RO':'11','AC':'12','AM':'13','RR':'14','PA':'15','AP':'16','TO':'17','MA':'21','PI':'22',
 'CE':'23','RN':'24','PB':'25','PE':'26','AL':'27','SE':'28','BA':'29','MG':'31','ES':'32','RJ':'33',
 'SP':'35','PR':'41','SC':'42','RS':'43','MS':'50','MT':'51','GO':'52','DF':'53'}
# Proxy BNCC Computação: UFs em atualização de referencial (CIEB/Movimento pela Base, dez/2024)
BNCC_ATUALIZA = {'AM','AL','AP','ES','MA','MG','MT','PR','PB','SC','SP','RN','TO'}

def main():
    base = load("base_clean.json")["recs"]
    v25  = load("v2025.json")
    ideb = load("ideb.json")
    rend = load("rend.json")
    inse = load("inse.json")
    con  = load("conect.json")
    sim  = load("sim_atend.json")

    bncc = {}
    for sig, cod in SIG2COD.items():
        at = sig in BNCC_ATUALIZA
        bncc[cod] = {"st": 1 if at else 0,
                     "lab": ("Em atualização do referencial de Computação (assessoria CIEB/MpB, 2024)" if at
                             else "Computação transversal no referencial estadual (sem componente específico identificado nesta fonte)")}

    r0 = lambda x: round(x) if x else 0
    yn = lambda v: 1 if str(v).lower().startswith("s") else 0
    pend_list, pend_idx = [], {}
    def pcode(s):
        s = (s or "").strip()
        if not s: return -1
        if s not in pend_idx: pend_idx[s] = len(pend_list); pend_list.append(s)
        return pend_idx[s]

    cols = ["uf","ib","nm","rd","vf","vt","vr","tot","ia","ip","c1","c2","c3","c4","c5","hab","ben",
            "pend","vr25","tr","ai","af","em","aim","ail","afm","afl","emm","eml","apf","rpf","abf",
            "apm","abm","nse","drec","iei","rc","inse","cnet","capr","cdown","cn",
            "eva","evp","vra","vrp","vta","vtc","vtei","meb","m17","m18","m19","m20","m21","m22","m23"]
    rows = []; trans = Counter(); tsum = {"perdeu":0,"entrou":0}
    for o in base:
        ib = o["IBGE"]; v2026 = o["Compl_VAAR"] or 0; v2025 = v25.get(ib,0) or 0
        b26, b25 = v2026>0, v2025>0
        tr = "mantem" if (b25 and b26) else ("perdeu" if (b25 and not b26) else ("entrou" if (not b25 and b26) else "fora"))
        trans[tr]+=1
        if tr=="perdeu": tsum["perdeu"]+=v2025
        if tr=="entrou": tsum["entrou"]+=v2026
        I=ideb.get(ib,{}); R=rend.get(ib,{}); N=inse.get(ib,{}); K=con.get(ib,{}); S=sim.get(ib,{})
        rows.append([o["UF"],ib,o["Entidade"],("E" if o["Rede"]=="Estadual" else "M"),
            r0(o["Compl_VAAF"]),r0(o["Compl_VAAT"]),r0(v2026),r0(o["Compl_Uniao_Total"]),
            round(o["VAAR_ind_atend"] or 0,4),round(o["VAAR_ind_aprend"] or 0,4),
            yn(o["Cond_I"]),yn(o["Cond_II"]),yn(o["Cond_III"]),yn(o["Cond_IV"]),yn(o["Cond_V"]),
            (1 if o["Habilitado_VAAR"].lower().startswith("habilit") else 0),
            (1 if o["Benef_VAAR"].lower().startswith("benef") else 0),pcode(o["Pend_VAAR"]),
            r0(v2025),{"mantem":0,"perdeu":1,"entrou":2,"fora":3}[tr],
            I.get("ai_ideb"),I.get("af_ideb"),I.get("em_ideb"),
            I.get("ai_mat"),I.get("ai_lp"),I.get("af_mat"),I.get("af_lp"),I.get("em_mat"),I.get("em_lp"),
            R.get("ap_fun"),R.get("rp_fun"),R.get("ab_fun"),R.get("ap_med"),R.get("ab_med"),
            round(o["Pond_NSE"] or 0,4),round(o["Pond_Drec"] or 0,4),round((o["IEI_pct"] or 0),4),r0(o["Receita_Contrib"]),
            N.get("inse_mun"),K.get("cn_net"),K.get("cn_aprend"),K.get("cn_down"),K.get("cn_n"),
            yn(o.get("VAAR_evoluiu_atend")), yn(o.get("VAAR_evoluiu_aprend")),
            r0(o.get("Est_VAAR_atend")), r0(o.get("Est_VAAR_aprend")),
            round(o.get("VAAT_antes") or 0, 2), round(o.get("VAAT_com_compl") or 0, 2),
            r0(o.get("Compl_VAAT_EI")),
            S.get("mat_eb", 0), S.get("m17", 0), S.get("m18", 0), S.get("m19", 0),
            S.get("m20", 0), S.get("m21", 0), S.get("m22", 0), S.get("m23", 0)])

    nat = dict(
        vaaf=sum(o["Compl_VAAF"] or 0 for o in base), vaat=sum(o["Compl_VAAT"] or 0 for o in base),
        vaar=sum(o["Compl_VAAR"] or 0 for o in base), total=sum(o["Compl_Uniao_Total"] or 0 for o in base),
        rc=sum(o["Receita_Contrib"] or 0 for o in base),
        vaar_atend=sum(o.get("Est_VAAR_atend") or 0 for o in base),
        vaar_aprend=sum(o.get("Est_VAAR_aprend") or 0 for o in base),
        n=len(base), hab=sum(1 for o in base if o["Habilitado_VAAR"].lower().startswith("habilit")),
        naohab=sum(1 for o in base if "não" in o["Habilitado_VAAR"].lower()),
        vaar2025=sum(v25.values()), trans=dict(trans), tsum={k:round(v) for k,v in tsum.items()},
        bncc_atualiza=len(BNCC_ATUALIZA))
    mn=[con[k] for k in con if len(k)==7]
    sn=sum(c["cn_n"] for c in mn);
    nat["cn_aprend"]=round(sum(c["cn_aprend"]*c["cn_n"] for c in mn)/sn,1)
    nat["cn_net"]=round(sum(c["cn_net"]*c["cn_n"] for c in mn)/sn,1)

    byuf = defaultdict(lambda: dict(vaaf=0,vaat=0,vaar=0,total=0,rc=0,n=0,hab=0,naohab=0,vaar25=0,perdeu=0,
        ia_s=0,ia_n=0,af_s=0,af_n=0,em_s=0,em_n=0,ab_s=0,ab_n=0,in_s=0,in_n=0,ca_s=0,ca_w=0))
    ti = cols.index("tr")
    for o,row in zip(base,rows):
        a=byuf[o["UF"]]
        for k,c in [("vaaf","Compl_VAAF"),("vaat","Compl_VAAT"),("vaar","Compl_VAAR"),("total","Compl_Uniao_Total"),("rc","Receita_Contrib")]:
            a[k]+=o[c] or 0
        a["n"]+=1; a["vaar25"]+=v25.get(o["IBGE"],0) or 0
        if o["Habilitado_VAAR"].lower().startswith("habilit"): a["hab"]+=1
        else: a["naohab"]+=1
        if row[ti]==1: a["perdeu"]+=1
        if o["Rede"]=="Municipal":
            I=ideb.get(o["IBGE"],{}); ab=rend.get(o["IBGE"],{}).get("ab_fun"); iv=inse.get(o["IBGE"],{}).get("inse_mun"); K=con.get(o["IBGE"])
            if I.get("ai_ideb"): a["ia_s"]+=I["ai_ideb"]; a["ia_n"]+=1
            if I.get("af_ideb"): a["af_s"]+=I["af_ideb"]; a["af_n"]+=1
            if I.get("em_ideb"): a["em_s"]+=I["em_ideb"]; a["em_n"]+=1
            if ab is not None: a["ab_s"]+=ab; a["ab_n"]+=1
            if iv is not None: a["in_s"]+=iv; a["in_n"]+=1
            if K and K.get("cn_aprend") is not None: a["ca_s"]+=K["cn_aprend"]*K["cn_n"]; a["ca_w"]+=K["cn_n"]
    mean=lambda s,n,d: round(s/n,d) if n else None
    out_byuf={}
    for u,a in byuf.items():
        out_byuf[u]=dict(
            vaaf=round(a["vaaf"]),vaat=round(a["vaat"]),vaar=round(a["vaar"]),total=round(a["total"]),rc=round(a["rc"]),
            vaar25=round(a["vaar25"]),n=a["n"],hab=a["hab"],naohab=a["naohab"],perdeu=a["perdeu"],
            ideb_ai=mean(a["ia_s"],a["ia_n"],2),ideb_af=mean(a["af_s"],a["af_n"],2),ideb_em=mean(a["em_s"],a["em_n"],2),
            ab_med=mean(a["ab_s"],a["ab_n"],2),inse=mean(a["in_s"],a["in_n"],3),
            capr=mean(a["ca_s"],a["ca_w"],1),bncc=bncc.get(SIG2COD.get(u,""),{}).get("st",0))

    payload=dict(cols=cols,rows=rows,pend=pend_list,
        nat={k:(round(v,1) if isinstance(v,float) else v) for k,v in nat.items()},
        byuf=out_byuf,bncc=bncc)
    outp=PROC/"payload.json"
    json.dump(payload,open(outp,"w",encoding="utf-8"),ensure_ascii=False,separators=(",",":"))
    print(f"payload.json escrito: {outp}  ({len(rows)} entes, {len(cols)} colunas)")

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""
Injeta payload.json + malhas geográficas no template e gera o painel final.

Entra: panel/template.html  (com marcadores /*__PAYLOAD__*/, /*__GEOUF__*/, /*__GEOMUN__*/)
       data/processed/payload.json, data/processed/geo/uf_simpl.json, mun_simpl.json
Sai:   dist/painel_fundeb_2026.html  (HTML autocontido, abre em qualquer navegador)

Uso:   python src/build_panel.py
Sem dependências externas.
"""
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"

def main():
    tpl  = (ROOT/"panel"/"template.html").read_text(encoding="utf-8")
    pay  = (PROC/"payload.json").read_text(encoding="utf-8")
    guf  = (PROC/"geo"/"uf_simpl.json").read_text(encoding="utf-8")
    gmun = (PROC/"geo"/"mun_simpl.json").read_text(encoding="utf-8")
    for name,blob in [("payload",pay),("uf",guf),("mun",gmun)]:
        if "</script>" in blob:
            raise SystemExit(f"Conteúdo de {name} contém </script> — abortando por segurança.")
    html = (tpl.replace("/*__PAYLOAD__*/", pay)
               .replace("/*__GEOUF__*/", guf)
               .replace("/*__GEOMUN__*/", gmun))
    out = ROOT/"dist"/"painel_fundeb_2026.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"painel escrito: {out}  ({len(html.encode('utf-8'))//1024} KB)")

if __name__=="__main__":
    main()

"""Extract TRANSLATIONS from utils/i18n.py via ast (no streamlit import) and
emit web/js/i18n.js. Keeping this generated means the NL/EN strings can never
drift between the two front-ends during the migration."""
import ast, json, pathlib

src = pathlib.Path("utils/i18n.py").read_text(encoding="utf-8")
tree = ast.parse(src)
translations = None
for node in tree.body:
    if isinstance(node, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "TRANSLATIONS" for t in node.targets
    ):
        translations = ast.literal_eval(node.value)
if translations is None:
    raise SystemExit("TRANSLATIONS not found")

nl, en = translations["nl"], translations["en"]
missing_en = sorted(set(nl) - set(en))
missing_nl = sorted(set(en) - set(nl))
if missing_en or missing_nl:
    raise SystemExit(f"parity broken: missing en={missing_en} missing nl={missing_nl}")

print(f"languages={list(translations)} keys={len(nl)}")
body = json.dumps(translations, ensure_ascii=False, indent=2, sort_keys=False)
out = pathlib.Path("web/js/i18n-data.js")
out.write_text(
    "// GENERATED FILE - do not edit by hand.\n"
    "// Regenerate with: python3 tools/gen_i18n.py\n"
    "// Source of truth: utils/i18n.py (TRANSLATIONS)\n"
    f"export const TRANSLATIONS = {body};\n",
    encoding="utf-8",
)
print(f"wrote {out} ({out.stat().st_size} bytes)")

"""Terminal version, for when you don't want to open a browser."""
import textwrap

from careqa.assistant import Assistant


def main():
    bot = Assistant()
    if not bot.languages():
        print("No data found. Run: python scripts/fetch_data.py")
        return
    print("Ask about Alzheimer's or dementia care (English / বাংলা / 中文). Empty line to quit.")
    print("General information only, not medical advice.\n")
    while True:
        try:
            q = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            break
        r = bot.ask(q)
        if r["urgent"]:
            print("\n!! " + r["urgent"])
        if r["found"]:
            print(f"\n[{r['matched']}]")
        for para in r["answer"].split("\n\n"):
            # textwrap doesn't know how wide CJK is, so leave zh alone
            print(para if r["lang"] == "zh" else textwrap.fill(para, 88))
            print()
        if r.get("url"):
            print(f"source: {r['source']}  {r['url']}")
        if r["related"]:
            print("see also: " + " | ".join(r["related"]))
        print()


if __name__ == "__main__":
    main()

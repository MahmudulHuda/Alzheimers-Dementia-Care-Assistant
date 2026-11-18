const UI = {
  en: {
    title: "Dementia Care Q&A",
    intro: "For families and caregivers of people living with Alzheimer's or another dementia. Ask in English, Bangla or Chinese.",
    placeholder: "Type your question…",
    send: "Ask",
    source: "Source",
    matched: "Closest question",
    related: "You could also ask",
    more: "Show more",
    less: "Show less",
    error: "Something went wrong. Is the server still running?",
    disclaimer: "General information from US National Institutes of Health material. It is not medical advice and can't replace a doctor.",
    mt: "",
  },
  bn: {
    title: "ডিমেনশিয়া পরিচর্যা প্রশ্নোত্তর",
    intro: "আলঝেইমার বা অন্য ডিমেনশিয়ায় আক্রান্ত মানুষের পরিবার ও পরিচর্যাকারীদের জন্য। বাংলা, ইংরেজি বা চীনা ভাষায় প্রশ্ন করুন।",
    placeholder: "আপনার প্রশ্ন লিখুন…",
    send: "জিজ্ঞাসা করুন",
    source: "সূত্র",
    matched: "সবচেয়ে কাছের প্রশ্ন",
    related: "এগুলোও জিজ্ঞাসা করতে পারেন",
    more: "আরও দেখুন",
    less: "কম দেখুন",
    error: "কিছু একটা সমস্যা হয়েছে। সার্ভার চালু আছে তো?",
    disclaimer: "এখানে যুক্তরাষ্ট্রের ন্যাশনাল ইনস্টিটিউটস অব হেলথের সাধারণ তথ্য দেওয়া হয়। এটি চিকিৎসা পরামর্শ নয়, ডাক্তারের বিকল্পও নয়।",
    mt: "উত্তরটি ইংরেজি থেকে যন্ত্রানুবাদ করা, ভুল থাকতে পারে।",
  },
  zh: {
    title: "认知症照护问答",
    intro: "为阿尔茨海默病及其他认知症患者的家属和照护者提供参考。可用中文、英文或孟加拉语提问。",
    placeholder: "请输入您的问题…",
    send: "提问",
    source: "来源",
    matched: "最接近的问题",
    related: "您还可以问",
    more: "展开",
    less: "收起",
    error: "出错了，请确认服务仍在运行。",
    disclaimer: "内容为美国国立卫生研究院的一般健康信息，不构成医疗建议，也不能代替医生。",
    mt: "答案由英文机器翻译而来，可能有不准确之处。",
  },
};

const $ = (id) => document.getElementById(id);
const chat = $("chat");
let uiLang = "en";

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
}

function setUiLang(lang) {
  uiLang = lang;
  const t = UI[lang];
  document.documentElement.lang = lang;
  $("title").textContent = t.title;
  $("intro").textContent = t.intro;
  $("q").placeholder = t.placeholder;
  $("send").textContent = t.send;
  $("disclaimer").textContent = t.disclaimer;
  loadChips(lang);
}

async function loadChips(lang) {
  const box = $("chips");
  box.innerHTML = "";
  try {
    const res = await fetch("/examples?lang=" + lang);
    for (const q of await res.json()) box.appendChild(chip(q));
  } catch (e) { /* chips are optional */ }
}

function chip(text) {
  const b = el("button", "chip", text);
  b.type = "button";
  b.onclick = () => send(text);
  return b;
}

function addUser(text) {
  chat.appendChild(el("div", "msg user", text));
}

function addBot(r) {
  const t = UI[r.lang] || UI.en;
  const box = el("div", "msg bot");

  if (r.urgent) box.appendChild(el("div", "urgent", r.urgent));
  if (r.found) box.appendChild(el("div", "matched", t.matched + ": " + r.matched));

  const body = el("div", "answer");
  for (const para of r.answer.split("\n\n")) body.appendChild(el("p", "", para));
  box.appendChild(body);

  if (r.answer.length > 700) {
    body.classList.add("clipped");
    const toggle = el("button", "toggle", t.more);
    toggle.type = "button";
    toggle.onclick = () => {
      const open = body.classList.toggle("clipped");
      toggle.textContent = open ? t.more : t.less;
    };
    box.appendChild(toggle);
  }

  if (r.found) {
    const meta = el("div", "meta");
    if (r.url) {
      meta.append(t.source + ": ");
      const a = el("a", "", r.source || r.url);
      a.href = r.url; a.target = "_blank"; a.rel = "noopener";
      meta.appendChild(a);
    }
    if (t.mt) meta.appendChild(el("span", "mt", " " + t.mt));
    box.appendChild(meta);
  }

  if (r.related && r.related.length) {
    const rel = el("div", "related");
    rel.appendChild(el("span", "", t.related + ":"));
    r.related.forEach((q) => rel.appendChild(chip(q)));
    box.appendChild(rel);
  }

  chat.appendChild(box);
  box.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function send(text) {
  text = text.trim();
  if (!text) return;
  addUser(text);
  $("q").value = "";
  $("send").disabled = true;
  const picked = $("lang").value;
  try {
    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ q: text, lang: picked === "auto" ? null : picked }),
    });
    const r = await res.json();
    if (r.error) throw new Error(r.error);
    addBot(r);
    // in auto mode follow whatever language the person just used
    if (picked === "auto" && r.lang !== uiLang) setUiLang(r.lang);
  } catch (e) {
    chat.appendChild(el("div", "msg bot error", UI[uiLang].error));
  } finally {
    $("send").disabled = false;
    $("q").focus();
  }
}

$("form").addEventListener("submit", (e) => { e.preventDefault(); send($("q").value); });
$("lang").addEventListener("change", (e) => {
  if (e.target.value !== "auto") setUiLang(e.target.value);
});

setUiLang(AVAILABLE.includes("en") || !AVAILABLE.length ? "en" : AVAILABLE[0]);

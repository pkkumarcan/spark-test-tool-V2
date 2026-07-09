# X91 — Legal & Compliance

**Purpose:** YouTube AI content policy, disclosure requirements, YMYL disclaimers, and IP considerations.  
**Created:** 2026-07-09 (V3 — based on vidIQ compliance framework)  
**Estimated time:** 15 minutes

---

## YouTube AI Content Policy (2026)

### What Requires Disclosure

YouTube requires disclosure of "significantly altered or synthetic" content:

| Content Type | Disclosure Required | How |
|-------------|-------------------|-----|
| AI-generated visuals | ✅ Yes | Enable "Contains AI-generated content" toggle |
| AI voiceover | ✅ Yes | Same toggle |
| AI-written scripts | ⚠️ Recommended | Include in description |
| AI-generated music | ✅ Yes | If rights owned (Suno, AudioCraft) |
| AI deepfakes of real people | ❌ Prohibited | Never do this |
| Stock footage manipulation | ⚠️ Case-by-case | If significantly altered |

### How to Disclose

In YouTube Studio for each video:
1. Go to "Details" → "Show more"
2. Find "Altered content" section
3. Enable "Yes, it includes altered content"
4. Select "Altered synthetic media" → "Includes AI-generated content"
5. Save

### What YouTube Will NOT Demonetize (2026)

- ✅ AI voiceover (common and accepted)
- ✅ AI-generated images/visuals (with disclosure)
- ✅ AI-written scripts (no rule against this)
- ✅ AI-generated music (if you own rights)

### What Risks Demonetization

- ⚠️ Fully automated channel with no human oversight
- ⚠️ Repetitive, low-effort content (same template, minimal variation)
- ❌ Medically inaccurate health claims (PKP channel)
- ❌ Financial advice without disclaimers (GDB content)
- ❌ AI deepfakes of real people without consent
- ❌ Publishing more than 3-4 videos/day per channel (spam filter trigger)

---

## YMYL (Your Money Your Life) Compliance

### Health Content (PKP — Peak Protocol)

**Required disclaimers:**

**In every video description:**
```
⚠️ Disclaimer: This content is for educational and informational purposes only.
It is not intended as medical advice. Always consult with a qualified healthcare
professional before making any changes to your diet, exercise, or health regimen.
Individual results may vary.
```

**Verbally at start of video (recommended):**
```
"Quick note: everything I share here is for educational purposes.
This is not medical advice — always consult your doctor before
making changes to your health routine."
```

**Topics requiring extra caution:**
- Supplements and dosages
- Fasting protocols
- Cold exposure
- Sleep medications
- Any claim about treating/curing conditions

### Finance Content (GDB — Ground Brief)

**Required disclaimers:**

**In every video description:**
```
⚠️ Disclaimer: This content is for educational and informational purposes only.
It does not constitute financial advice, investment advice, or any other sort of advice.
Always consult with a qualified financial advisor before making investment decisions.
Past performance is not indicative of future results.
```

**Topics requiring extra caution:**
- Specific investment recommendations
- Cryptocurrency advice
- Tax strategies
- Insurance products
- Real estate advice

---

## Copyright & Fair Use

### What You CAN Use

- **Public domain content** — No copyright restrictions
- **Creative Commons licensed content** — With attribution
- **Your own AI-generated content** — You own the output
- **Fair use** — Commentary, criticism, education (limited)

### What You CANNOT Use

- **Copyrighted music** — Without license
- **Copyrighted video footage** — Without license
- **Trademarked logos** — Without permission
- **Other creators' content** — Without permission

### Safe Sources for Visuals

| Source | License | Cost |
|--------|---------|------|
| Pexels | Free commercial use | $0 |
| Unsplash | Free commercial use | $0 |
| Pixabay | Free commercial use | $0 |
| Stable Diffusion output | You own it | $0 (local) |
| ComfyUI output | You own it | $0 (local) |

### Music Licensing

| Source | License | Cost |
|--------|---------|------|
| AudioCraft/MusicGen | You own output | $0 |
| Suno AI | You own output | $10/mo |
| Epidemic Sound | Licensed | $15/mo |
| Artlist | Licensed | $10/mo |

---

## Privacy & Data Protection

### Viewer Data
- YouTube collects viewer analytics (you don't access raw data)
- Comply with GDPR/CCPA if targeting EU/CA viewers
- Don't collect viewer personal information outside YouTube

### Your Data
- API keys in `.env` — never commit to git
- YouTube OAuth tokens — store securely
- Video files — back up regularly

---

## Contractual Considerations

### YouTube Terms of Service
- Comply with YouTube Community Guidelines
- Don't manipulate metrics (fake views, bot subscribers)
- Don't spam (more than 3-4 videos/day per channel)
- Don't mislead viewers about content authenticity

### Sponsorship Disclosures
- Include #ad or #sponsored in description
- Verbal disclosure at start of sponsored segment
- FTC requires clear disclosure of material connections

### Affiliate Links
- Include disclosure: "This video contains affiliate links"
- Place disclosure near the links
- Don't make false claims about products

---

## Compliance Checklist (Per Video)

### Before Publishing
- [ ] AI disclosure enabled in YouTube Studio
- [ ] Health disclaimer included (PKP videos)
- [ ] Finance disclaimer included (GDB videos)
- [ ] No copyrighted material used without license
- [ ] No false claims about AI visuals being real
- [ ] No deepfakes of real people
- [ ] Not publishing more than 3-4 videos/day

### Sponsorship/Affiliate
- [ ] #ad or #sponsored in description (if applicable)
- [ ] Affiliate disclosure near links
- [ ] Verbal disclosure for sponsored segments
- [ ] FTC-compliant disclosure placement

---

## Incident Response: Copyright Strike

If you receive a copyright strike:
1. Don't panic — it's usually automated
2. Review the claim details
3. If fair use: file a counter-notification
4. If valid: remove the content
5. Three strikes = channel termination

**Prevention:** Use only your own AI-generated content, public domain, or properly licensed material.

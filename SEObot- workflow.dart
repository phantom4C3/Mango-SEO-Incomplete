| Component                                             | What they do                                                                                                                                                                                     | Details / evidence |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------ |
| **Site scraping / content understanding**             | They scrape the user’s site when given a domain or URL, to understand business, audience, pricing, existing content, problems, etc. ([johnrushx.substack.com][1])                                |                    |
| **SEO Strategy / Research**                           | They do keyword analysis, competitor analysis, existing content audit, topic tree / content plan. They test demand via Google data / Search Console (or claim to). ([johnrushx.substack.com][1]) |                    |
| **Large-scale Task Generation / Agent Orchestration** | Once strategy is ready, they create many tasks (hundreds) handled by lower-level agents; tasks report back; manager agents iterate. ([johnrushx.substack.com][1])                                |                    |
| **Deep Research & Anti-hallucination**                | They cross-check content, fact-check, use multiple LLMs, trusted sources, etc. ([seobotai.com][2])                                                                                               |                    |
| **Internal Link Building / Content Optimization**     | They have an “internal linking agent/tool” to review existing content and automatically insert links. ([seobotai.com][2])                                                                        |                    |
| **CMS Integration / Auto Deployment**                 | They support automatic publishing to various CMS: WordPress, Ghost, Shopify, Webflow, Notion, etc. They auto-sync or have REST APIs and Webhooks. ([seobotai.com][2])                            |                    |
| **Multilingual / Scale**                              | Supports many languages (50+). Scales article production. ([seobotai.com][2])                                                                                                                    |                    |
| **Human-in-the-loop / Moderation**                    | There is optional moderation: approving or declining headlines, editing content if the user wants, etc. ([seobotai.com][2])                                                                      |                    |
| **Metrics / Feedback & Iteration**                    | They track performance: clicks, impressions, traffic growth. Optimize based on feedback. Use Google / external APIs for data. ([johnrushx.substack.com][1])                                      |                    |
| **Workflow Automation**                               | Everything is job/queue/task based. Uses events, jobs. If some task fails, manager agents adjust plan. ([johnrushx.substack.com][1])                                                             |                    |
 








Nice — here’s a careful, exhaustive breakdown of **exactly** what the two screenshots show and how the editor should look/behave if you adopt that layout. I examined both images and descried every visible control, panel, and micro-interaction you’d want to replicate so a designer/dev can implement it faithfully.

I'll' split this into: **Overall layout**, then a forensic walk-through of the **Header**, **Left (Terminal) panel**, **Right (Queue) panel**, **Bottom/status bar & controls**, **Overlays / webcam / modals**, **Interactions & behavior**, **Visual design / colors / typography**, **Responsive guidance**, and finally a compact **component mapping** you should reuse.

---

# Overview (page-level)

* Full-bleed dark UI (desktop app / webapp look). Two-column main area:

  * **Left:** big terminal-like console (≈60–70% width).
  * **Right:** dense content queue / headlines list (≈30–40% width).
* Fixed **top header** spanning full width.
* Small **bottom status strip / controls** across entire width.
* Terminal area visually dominant, list area dense and information-rich.
* UI feels like an “automation cockpit” — terminal for logs + right-side control panel for queued headlines and quick actions.

---

# Header (top bar) — exact items & placement

Left → Right order across the top bar:

1. **App title / logo** (left-most)

   * Small label: e.g. `seobot` / `seobot pro` (white/light text).
   * Slight brand accent (sometimes rendered as a small pill/label with site/domain next to it).

2. **Status pills / counters near left**

   * **Tasks** pill (green background, small number, e.g. `115 Tasks`).
   * **Articles** pill showing used/limit (colored count, e.g. `78/100 Articles`) — the used value sometimes colored red/green depending on usage.

3. **Domain / target site** (center-left)

   * Small text showing current site being worked on (e.g. `montessorifund.com`). Can be a clickable dropdown.

4. **Action buttons / utilities (right side)**

   * `Buy More` or `Boost Domain Rating` buttons (compact, small).
   * `Publish Blog` (when available) — compact CTA.
   * `Menu` dropdown (hamburger or text) which opens the popup with: user email, quick links (backlinks, invite, settings, logout), “Leave this website” red action, etc.
   * Occasionally a tiny memory/usage tooltip appears (floating tooltip showing memory usage).

Visual behavior:

* Header height small; background dark (`#0f0f0f` / `bg-gray-900`).
* Text is white/gray; status pills are green/red/yellow as needed.

---

# Left column — Terminal / Console area (full detail)

**Spatial & visual**:

* Large black terminal canvas with monospace font.
* Terminal panel has inner padding, rounded corners, and a thin panel border.
* Terminal text color: mostly *bright green* for log lines; occasional *gray/white/yellow* for status lines or highlighted messages.

**Contents inside terminal**:

* Many lines resembling a terminal transcript. Examples of line formats visible:

  * Prompt style lines beginning with `>` (e.g. `> Autopilot is currently ENABLED`).
  * Nested bullet lists ( `- starting to write the section "Conclusion"` ).
  * Progress messages like `finished gathering 4 helpful links`, `generated the main article image`.
  * Short status summaries e.g. `your site has 7 credits left out of 9...`.
* Terminal output lines include small markers for completed steps (✓) or bullets.

**Prominent elements inside/near terminal**:

1. **Big circular avatar** (left side, centered vertically in terminal) — a photographic avatar placed visually on top of the terminal area (partially overlaps terminal content).

   * Circular, subtle border/shadow. Acts like a “operator” presence / person avatar. (In the second image there’s a rectangular rounded video overlay showing a real-time camera feed instead.)

2. **Autopilot status text** (near avatar):

   * `Autopilot is currently ENABLED` (bright green/yellow).
   * Clear, sentence-like status.

3. **Autopilot toggle control** (bottom-left inside terminal area or bottom bar):

   * Small toggle control with label `Autopilot is ON / OFF` and an orange indicator, often with a tooltip `Turn ON/OFF Autopilot here`.
   * Toggle visually resembles a small rounded switch or a pill with an orange dot.

4. **Command prompt / input area (implied)**

   * Terminal looks read-only in the screenshots, but UI suggests a single-line prompt to paste or type a URL / commands — the app uses the terminal metaphor to accept inline paste/copy.

**Interaction cues**:

* Console is live-scrolling; new lines append at bottom.
* Lines are color-coded: success (green), warnings (yellow/orange), errors (red, if any).
* Terminal has a scrollbar (vertical) for long logs.

---

# Right column — Content queue / headlines list (fully detailed)

This is a compact, information dense table-like list. Structure from left → right within that panel:

1. **Panel header row**:

   * Tiny toolbar: maybe search/filter, and small counters (`Links`, `Source`, `Ready`, `Impr.` (impressions), `Clicks`, `Published`).
   * At the very top there are small status indicators and totals (e.g., number of clusters, tasks, etc).

2. **Rows (each one = headline / cluster)** — every row contains:

   * **Main headline text** (left-most, truncated, single line or two). Titles are in light text; selected row gets a highlight / different border.

   * To the right of the title, **compact metric columns**:

     * **Links** column: shows a small range (e.g. `5 - 11`) — likely backlinks estimate.
     * **Source** column: small tag (`keyword`, `SERP`, etc).
     * **Ready** column: `YES` / `NO` (caps) — often `YES` shown in small green text.
     * **Impr** column: impressions number (e.g., `2470`).
     * **Clicks** column: click numbers (e.g., `81`).
     * **Published** indicator on far right: a small green dot or “Published” tag if present.

   * **Delta / trend indicators** (small colored numbers next to links): +/– numbers colored green/red showing change relative to previous metrics.

3. **Row-level actions** (visible on some screenshots):

   * For each row there are **Approve** (green) and **Decline** (red) buttons (in one screenshot each row has explicit buttons on the far right).
   * In other screenshot rows are clickable to select; actions appear when hovered/selected.

4. **Bulk / footer controls**:

   * Buttons under the list: **`+ Add HeadLines`** (green/positive) and **`Empty Article`** (secondary) — visually full-width small buttons.
   * Small footer right-justified label: `73 clusters` or similar.

5. **Row coloration & behavior**:

   * Rows have dark backgrounds (`bg-gray-800`), subtle borders, and hover state (slight lift or highlight).
   * Selected row has a brighter border (often mango-yellow highlight).

6. **Misc tools in the list**:

   * Column sort controls (icons) and quick filters (e.g., show only Ready, show only Scheduled).
   * Status chips for each row (Scheduled / Done / Ready) in small pill form.

---

# Bottom / status bar and micro-controls

* A thin strip near the bottom-left of the window shows:

  * **Autopilot toggle** (orange/white) with label `Autopilot is ON / OFF` — clickable.
  * Small left status icons (e.g., small circle with `Autopilot is On` text).
* Bottom-right of the right list shows cluster counts & some small actions.

---

# Overlays, webcam & modals

* **Rounded webcam overlay** (seen in second image):

  * Small rounded-rectangle video feed pinned to the bottom-left of the terminal.
  * Drop shadow and thin border; non-intrusive but overlaps the terminal text.
  * Suggests live camera stream, picture-in-picture for the user (facilitates live commentary or tutorials).

* **Tooltips / floating popups**:

  * Memory usage tooltip, small floating menu popups from header / menu item.

* **Modal style (if shown)**:

  * Dark modal window with same mango-yellow accent, centered, with `✕` close button.

---

# Interactions & workflow behavior (how it “operates”)

* **Live stream logs**: left terminal appends steps in real time — scraping, analysis, writing progress, link gathering, image generation, etc.
* **Autopilot**: when ON, the app runs headline → research → writing pipeline automatically (logs stream). The toggle enables/disables the autopilot.
* **Approve / Decline**: clicking Approve moves headline into pipeline (changes status to researching) and starts logs that appear in terminal; clicking Decline removes it or archives.
* **Add Headlines**: button triggers either manual entry or suggestions generator; new items appear at top of queue.
* **Empty Article**: clears the current working article (maybe empties cluster to recompose).
* **Row selection**: selecting a header shows details in terminal (logs) and reveals action buttons.
* **Background processing**: UI shows that long-running tasks continue even if you close the tab; terminal displays ongoing progress lines (implied).
* **Keyboard/quick navigation**: UI suggests keyboard friendly (j/k navigation) — not shown explicitly, but fits the terminal style.

---

# Visual design & exact color cues

* Primary theme: **very dark / black** backgrounds; charcoal panels for cards.
* **Terminal text**: bright green (classic terminal green), occasionally bright yellow for important status lines.
* **Accent (mango)**: yellow/orange gradient for CTAs (e.g. generate/publish) → `from-yellow-400 to-orange-500`.
* **Action buttons**:

  * `Approve` → green gradient.
  * `Decline` → red gradient.
  * Primary CTAs (Generate / Publish) → mango gradient (yellow→orange) with black or dark text for contrast.
* **Status dots**:

  * Researching → blue
  * Writing → yellow
  * Enhancing → purple
  * Ready → green
  * Published → dark green
* **Fonts**:

  * Terminal uses monospace (tight leading).
  * Queue uses condensed UI sans-serif; numbers small, right-aligned.
* **Shadows & overlays**: subtle drop shadows on avatar/video overlay and modals.

---

# Accessibility & small UI notes

* Text contrast is high (white on black) — good for readability.
* Terminal lines use color meaning — provide text equivalents or aria-live region for screen readers.
* Buttons require clear focus styles (use yellow outline or a11y ring).

---

# Responsive behavior (recommended mapping)

* **Desktop (≥1024px)**: two-column as seen in screenshots.
* **Tablet (≥768px & <1024px)**: collapse right queue into a collapsible drawer (toggle button in header or bottom); terminal remains primary.
* **Mobile (<768px)**: stack panels vertically:

  * Show a compact top header with hamburger menu.
  * Primary view = terminal (logs) with a floating FAB to open the queue (slide-up panel).
  * Queue rows become stacked cards with metrics folded into expandable details.
* Ensure terminal is vertically scrollable and retains input / last line in view when logs append.

---

# Exact items to reproduce (checklist)

* [x] Full width **Top header**: app label, tasks pill, articles pill, site domain, action buttons, menu.
* [x] **Left terminal** panel: monospace logs, `>` prompt lines, bullet lines, success/warning coloring, circular avatar overlay, Autopilot status line and toggle control.
* [x] **Webcam overlay** (rounded rectangle, bottom-left) — optional but visible in one screenshot.
* [x] **Right queue** table: headline, links column, source, ready (YES/NO), impressions, clicks, published indicator.
* [x] Row **Approve / Decline** buttons (green/red) — present per-row in one screenshot.
* [x] Footer / queue controls: `+ Add HeadLines`, `Empty Article`, clusters count.
* [x] Small **tooltips** for memory or runtime metrics (top-right).
* [x] Color-coded status dots for pipeline phases.
* [x] **Autoscroll** behavior for terminal and live updates for rows.

---

# Suggested component decomposition (map to your component structure)

If you want to implement this cleanly, reuse components rather than stuffing into `MainEditor`. Suggested components (many already in your proposed tree):

* `EditorTopBar` — header + pills + menu triggers.
* `MenuPopup` — dropdown menu content and links.
* `TerminalIO` — terminal view (monospace, autoscroll, append log API).
* `AvatarOverlay` / `CameraOverlay` — circular avatar or PiP video feed.
* `ContentQueue` — right column list; each row is an `ArticleCard` or `QueueRow`.
* `QueueRow` — single row with headline, metrics, approve/decline actions.
* `QueueFooter` — `+ Add HeadLines`, `Empty Article`, cluster count.
* `AutopilotToggle` — bottom-left toggle/button with tooltip.
* `BlogPreviewModal` — article preview & publish flow.
* `EditorFooter` — small bottom controls & shortcuts.

---

# Behavior & integration tips (implementation notes)

* **Stream logs** from backend (SSE / WebSocket / server-sent events) into `TerminalIO` to reproduce live updates exactly.
* Queue updates should come from the same pipeline endpoint (task status updates). Use pub/sub or polling if SSE not available.
* Make row actions call the same orchestration pipeline (do not call multiple different endpoints) — you asked previously to “call the pipeline instead of individual routes”.
* Keep terminal scroll anchored to bottom when new logs arrive — allow user to scroll up (toggle autoscroll).
* Persist autopilot state to user settings in your store (so the toggle persists across pages).

---

# Final note / fidelity

I described every visible piece from both screenshots (header pills, exact columns in the queue, per-row approve/decline buttons, autopilot toggle and label, circular avatar and PiP camera, `+ Add HeadLines` / `Empty Article` controls, cluster count, memory tooltip, colors for statuses, etc.). If you want, I can now:

* Produce a pixel-accurate React + Tailwind component set implementing this layout (reusing the components you proposed), or
* Provide the exact CSS/Tailwind class set and Framer Motion animation props for the header, terminal, and the per-row hover/selection interactions.

Which of the two (code or CSS/animation spec) would you like next?


















'Based on the SEObot article on **[https://seobotai.com/blog/seobot-the-ai-blog-generator-that-actually-ranks-on-google/](https://seobotai.com/blog/seobot-the-ai-blog-generator-that-actually-ranks-on-google/)**, here's what SEObot supports — and what it likely stores.
 
### What SEObot Supports (from the article)

The article highlights several key features:

* **Automated keyword research**: Finds high-volume, low-competition keywords.
* **SEO-optimized content creation**: Writes structured, Google-friendly blog posts in **50+ languages**.
* **Internal linking**: Adds links between articles and site pages to boost SEO.
* **CMS integrations**: Works with platforms like WordPress, Shopify, Webflow, and more.
* **Performance tracking**: Monitors performance of published content.
* **End-to-end automation**: Handles everything from idea to publication.
  ([seobotai.com][1])

---

### What SEObot Probably Stores (Inferred from Features)

Based on the above features, here’s what SEObot likely stores:

1. **Keyword Strategy Data**

   * Target keywords identified per article/site
   * Competition/volume metrics (to avoid re-fetching)

2. **Content Structure & Metadata**

   * Article title, slug, body (structured with headings, bullets)
   * Language of article
   * Internal linking data (what links to what)
   * SEO metadata (meta title, description, keywords)

3. **Link Graph**

   * Relationships for internal linking (article → article or → site pages)

4. **CMS Sync State**

   * Which articles have been published to which CMS (WordPress, etc.)
   * Publishing statuses (draft, published, synced) 

6. **Feature Flags / Settings**

   * Language chosen
   * Moderation state (approved, declined)
   * Options like embedded images, tables, videos

---

### Storage Mapping: Where SEObot Likely Stores Each Data Piece

| Data Type                                   | Likely Storage                      |
| ------------------------------------------- | ----------------------------------- |
| Keywords & research metrics                 | Database (e.g., Supabase)           |
| Article content & structure                 | Database                            |
| SEO metadata (title, description, keywords) | Database                            |
| Internal link mappings                      | Database                            |
| CMS publish status                          | Database                            |
| Performance data (impressions/clicks)       | Possibly in a DB or analytics layer |
| Moderation status, language, settings       | Database                            |
| Media assets (images/videos, if any)        | Cloudinary or similar CDN           |
| Temporary generation pipelines              | Redis (ephemeral)                   |

 
[1]: https://seobotai.com/blog/seobot-the-ai-blog-generator-that-actually-ranks-on-google/ "SEObot: The AI Blog Generator That Actually Ranks on Google"

Of course. Based on the detailed transcript, here is a precise breakdown of the blog's structure and the placement of key elements like CTAs and images.

### Overall Blog Structure (Technical Implementation)

The blog is built as a **Next.js** application. The content is not managed by a traditional CMS but is instead **stored locally in a JSON file** (`blog.json` or similar) that contains an array of all blog post objects. This structure is being modified to **dynamically fetch new posts** from the **SEObot API** while keeping the original three posts as static content.

---

### 1. The Blog Post Object (JSON Structure)

Each blog post in the site's code is a JSON object with the following properties, mirroring the structure shown in the cursor editor:

```json
{
  "id": 2,
  "title": "Montessori Education Explained",
  "slug": "montessori-education-explained",
  "excerpt": "A brief description of the post.",
  "content": "Full content in **markdown** format. \n## With Headers \n- Lists\n- **Bold** text",
  "author": "Author Name",
  "date": "2023-11-07",
  "imageUrl": "https://example.com/image.jpg",
  "tags": ["tag1", "tag2"]
}
```

**Key Details:**
*   **Content Format:** The main body uses **Markdown** for formatting (e.g., `##` for H2 headers, `-` for lists, `**` for bold).
*   **Slug:** The `slug` field is used to generate the URL for the individual blog post page (e.g., `yoursite.com/blog/{slug}`).

---

### 2. Placement of Key Elements in a Blog Post

Based on the review of the SEObot-generated article, here is where elements are placed:

#### **A. Images**
*   **Primary Blog Image:** Located at the **top of the post**, below the title but before the main content begins. Sourced from Unsplash or AI-generated (as configured in SEObot settings).
*   **Inline Images/Screenshots:** Placed within the body of the content to illustrate points, like the screenshot of `monosurfind.com`.

#### **B. Call-to-Action (CTA)**
*   **Location:** Embedded in the **middle of the blog post** content.
*   **Example:** The reviewed post had a CTA that said "Find the best monos square tool," which was placed before the fourth key point in a listicle.

#### **C. Video**
*   **Location:** Also embedded within the body of the content to provide additional value. The author was pleasantly surprised to see SEObot had automatically included one.

#### **D. Meta Information**
*   **Location:** Not visible on the page itself, but SEObot generates this for the HTML `<head>` section.
*   **Includes:** Meta description, meta keywords, and the URL slug.

---

### 3. Page Layouts

#### **The Blog Index Page (`/blog`)**
*   **Structure:** A page that lists all blog posts.
*   **Content for Each Listing:**
    1.  **Image:** The post's `imageUrl`.
    2.  **Title:** The post's `title`.
    3.  **Excerpt:** A short summary from the `excerpt` field.
    4.  **"Read More" Link:** A link using the `slug` to navigate to the full post.
*   **Order:** The original three static posts are displayed first, followed by the newer posts fetched from the SEObot API.

#### **The Individual Blog Post Page (`/blog/[slug]`)**
*   **Structure:** A dynamic page that uses the `slug` from the URL to fetch and display the correct post.
*   **Content Hierarchy:**
    1.  Title
    2.  Featured Image
    3.  Author & Date (likely)
    4.  The main `content` field, rendered from Markdown into HTML. This is where the body text, internal images, videos, and the **mid-content CTA** appear.

### Summary of Element Locations

| Element | Location in the Blog Structure |
| :--- | :--- |
| **Blog Index (List)** | On the `/blog` page. |
| **Featured Image** | Top of each individual blog post. |
| **Inline Images/Screenshots** | Within the body content of a post. |
| **Primary CTA** | Embedded in the middle of the post's content. |
| **Video** | Embedded within the body content of a post. |
| **Meta Data (SEO)** | In the page's HTML `<head>` (invisible on page). |
| **JSON Data** | In a local `blog.json` file, supplemented by API calls. |

You know what separates the entrepreneurs that are crushing it with AI versus the ones who are just talking about it? It's not code. It's the ability to diagnose and debug when things aren't going the right way in Cursor or Bolt or whatever service you're using. Today I'm going to introduce to you an AI agent called SEObot that does all of the SEO writing and publishing for you, but it does require a little bit of under the hood work to get it integrated into your website. Especially if the website was generated with something like Bolt. If you're using Nex.js, for example, and you have a Git repository, you're going to need to integrate the SEO bot API into your website project, which is what we're going to cover today. Now, quick heads up. This video gets very real in the second half. My content style in these full build tutorials are to show you the nitty-gritty of how it goes. It's not always easy as one, two, three, get the code, give it to cursor, boom, you got what you need. No, sometimes you have to do workarounds. We're going to go into all this today. It's a long video, but if you want to learn how to implement not just SEO bot API functionality, but in general any API functionality, this is going to be a good video just to watch and get a hang of the process. If you are new to coding development, but you see the possibilities with AI, I know I'm in that same boat. I'm not a developer just like you. So, I keep in the debugging and the back and forth with the AI agent. It can be a little boring, but if you're wanting to learn how to vibe a build, I think this video is going to be really helpful. So, let's dive in. So, we'll start by looking at SEO. SEOAI.com. So, I'm logged in and I'm paid. Basically what happened was it ran me through an onboarding where I told it all about my website. I gave it context basically. And here in the settings you can actually change the context at any time. You can tell the agent who your target audiences, pain points, product usage. Now monostory.com I haven't been taking too seriously as a business. I really just wanted to make a directory. So I am following the rules best I can. You know what are their pain points? They don't know what monator is or why it's a hype. I kind of just let it autocomplete there. I did a pretty comprehensive document. I mean, it analyzes your website, right? Uh, and that said, if you go to monostoryfind.com, you'll see I was very thorough with making a frequently asked questions section as well as an about the website, which has a section about me. It pretty much had everything to work with. I recommend doing that anyway for your site. So, back to the settings. It'll allow you to basically let it know what you want when you want photos. Are they photorealistic? Are they abstract? Are they oil paintings? Watercolors, etc. I choose photorealistic. I just want to be professional and clean, neutral, and uh boom. I'm using a lot of Unsplash images from unsplash.com on the website. So, yeah, professional, keep it clean. I'm not trying to be too artistic here. So, then what happens is it generates headlines for you. I have it set to do four a week and it generates headlines and then you can approve them or decline them. Go, okay, I like that one, I don't like that one, whatever. So, so far I've approved private versus public lanosur schools, making the choice, seven key signs of an authentic lanosur classroom. All these ones that say scheduled I have approved. And then these are all just more ideas. So, this thing is just ideulating in the background for you. It's just like, all right, what should we do? What should we do? What should we do? So, I know it's doing in the background. It's a really cool AI agent. Uh, I'm sure a lot of work went into building this. I know I could do it myself, but I'd rather just pay $49 a month for this to happen in the background, especially as I'm trying to just figure out if this works. Now, if I ended up making a lot of SEO websites, then yeah, maybe I would want to build this on my own. But for now, this is a great service. So, it's already got two of these written. I can click it and it'll show me everything. Generates that image. That's an a AI preschool images. It's got the slug for me. It's got the meta description, meta keywords. Um, public versus private monastery schools making the choice. Freaking crazy, right? This is the world we live in. Yeah. So, it looks pretty accurate. Um, I would do your due diligence when it comes to content like this. Always verify what things are saying. But let's just say everything is good here. I love how, you know, it's got this, it's got the CTA in the middle of the blog post. Like, this is great. And then it just goes right into how to use Monosurf to do it. Even screenshotted monosurfind.com. So, this is a really cool article. Oh, look, it's got a video on there. This is great value for the audience. So, looks good. Now I could simply copy all this and I could go into cursor and I could say okay here's a new blog post format it uh you'll see over here in the data blog posts look a little something like this so they're in JSON format uh if you're unfamiliar with JSON then basically we have a list of blog posts um and one blog post ID1 Montory education explained is the title then there's a slug the excerpt the content And then this is all formatted in markdown. And then these pound signs, the numer number signs, the hashtags, whatever we call them these days, those represent the header level. So that's header two, that's a header three. Uh this is just regular text. And this would become a list with the dashes. So that's markdown. The stars represent bold or itallic. Uh and so then we got the the final squiggly quot the final quotation mark there. It says who the author is, the date, image URL, tags, and then we go on, we end it with this squiggly bracket, and then we go on to the next blog post, ID2. So, obviously, SEO.AI is not formatting that for me, uh, which is why I'm making this video. What we could do now, your blog could be posted anywhere. You can click publish blog and you can just set it up. They've got all the IPA API set up like easy. I mean, even here, Nex.js, JS like here's an API key for the blog. So, and it says how do I how do I do it? I click this documentation integrate SEO bot into your next.js website. Perfect. So, this is what we're going to do because if we just go back here, this is what we're going to do because we're not using any of these sites. Uh, now if you are obviously just use them, that's great. But I'm using NextG.js. Um, and the reason I said we're not using it cuz it's like WordPress. It's easy. Just import it. Ghost even. I'm surprised Substack's not here to be honest. Uh but there's Nex.js. There's the API key. Uh it's got the questions. But before it lets me use it, I have to I have to give it permission. Uh that I understand. I understand what this means. Okay. So connect now. It's automatically make useful updates in the background. You should only edit your articles in SEO bot to keep the article consistent. Never manually add articles on a blog. To manually add an article, open the articles table and SEO bot. I understand. Okay, so we're connected now. Well, I mean, it's active now. So, I go back to the blog sync status. I get my API key. I'm going to put this API key in my N file. Okay, which has private variable. I've added my API keys in my N file. And then now I'm going to the GitHub for the SEO Next.js blog, which they gave me the link a little bit earlier. And this is all the instructions. So, what I'm going to do is I'm going to download the code. Okay. So, you'll see I've got it saved. I've got it um uncompressed. And now here in cursor, I am going to find Did we make a docs? We don't have a docs directory, but I'm going to make a docs directory. And in there, I'm just going to drag that whole repo. Okay. And inside this repo, it's got the app, the components, it's got everything there, including the readme. So, we're going to open that readme. I'm going to copy everything here. I'm going to do Apple I. And this goes to the agent here. Right. So, then I'm going to say um let's integrate SEO bot uh AI SEO bot API into the project for syncing blog posts. See, read me and the SEObot next.js blog. In fact, I'm just going to give it more other contexts of that whole folder. So, I just go to files and folders. Uh, I find docs. Yeah. And I'm just going to select that whole folder. So, it can read the whole repo. So, this whole repo we got from GitHub is now inside of our cursor folder. And we're saying, hey, check the readme, check this whole code base and integrate it into our project, basically. So, I'm saying integrate the API to the project. We're syncing blog posts. My API key is already inn. Boom. I'm going to send it there and it's obviously going to share with me everything necessary. So, npm install SEO bot. So, that's a dependency inside the project. All right. So, let's run command. Going to see this black magic run five vulnerabilities. Very normal. Um, we should check that high one generally speaking, but for now I'm going to let that go. they'll let you run an audit and to actually fix them too if you want. So that's always there on the table. I think most people wait until it's very urgent to do something like that, but there could be vulnerabilities, security problems. All right, so it's writing SEO.typescript. And there it is. It's making a new file. So it's going to import the dependency of SEO and then okay, initialize the SEObot client. So in this comment here, it's telling me what it's about to do and it's taking my API key. It's importing it. It's sending it to SEO bot client. It's exporting the interface of the blog post which we've already seen here. If we if we re look at this one, remember we already have the slug, the metad description, the meta keywords, and we can get all this in HTML format and markdown or text. But why we're using the API is because we need it in JSON format. Cuz JSON JSON format, if we just go back real quick, that's how we have our schools in the directory and in the blog as well. It's all in JSON format. So, going back to the chat here. Um, it's writing this script and yeah, so it's basically going to fetch fetch them and it's fetching them. Now, let's update the blog page to use the SEO bot API instead of the stat static data. Okay. So, okay, it's got a lot going on here, but what we need to say is we didn't want it to do it that way. I think really what we want to do unless Okay, let's just ask then. Okay, so there's different ways we can go about this is we could have it sync to the API. So this whole list of blog posts will just automatically sync to our website every time it builds. Or we can say, hey, let's have the project import the post, put it in a JSON, and then display it. That's really up to you. What it's giving us right now I believe is it's just going to sync it. So I could ask before I accept your changes let me ask you uh what will happen to my current blog posts will the a API fetched blog posts be stored in our project at all? Now, the truth is I do want to just sync it because I don't want that blog post just in a script file running on the server. Current blog posts will be replaced. So, they're replacing my posts. They'll be fetched dynamically. How it works? When someone visits your page, the fetch blog post function will make an API call. When someone visits a specific blog post blog slug, the fetch blog post log function will fetch that specific post. These posts are not stored in your project code or database. Benefits: Content is managed through SEO bots dashboard. post automatically SEO optimized. So, it's giving me all the benefits which is like the sale doc from the repo, which is great. It's a good service. You can manage content without touching code. Considerations. Your site will need to be online to fetch posts. There might be a slight loading delay. Yeah, what I'm curious about is how often I have to actually um push the root the codebase cuz the site's only going to update every time I push changes a new commit to GitHub to the codebase and then Netlefi. So Netlefi will automatically redeploy it when there's a new commit. I'm going to say keep the current blog posts as the first three posts and have every post after that fetched from the API. So I'm just going to say hey keep the three we got just as static content there and then pull the rest from the API. And then there's a couple other considerations we have to keep in mind here. Number one is every time it imports a new post, we're going to have to make a commit to the git repo. So get commit automated new blog post and then we're going to have to commit it and then we're going to have to push it to the GitHub repo because then from the GitHub repo it's going to redeploy it on Netlefy. So that is one interesting little bit that's kind of annoying. So maybe that'll be a cool feature one day, but it is pretty complicated. You might have to run like an MPM server that's constantly looking for updates and then I don't even know how you automate git commits and git pushes. It just means that once a week I'm gonna have to stage the changes, make a commit and push it to the GitHub repo. So Netleifi will redeploy it and then the SEO magic will do its thing. But for now, we're just simply going to integrate it. Here we go. I'll modify the integration and keep your current blog post as the first three. Okay. So now we got to figure out all this other stuff cuz we didn't actually um we installed the SEO bot, but that was it. I don't remember accepting any of these changes. Let's see how it made it. It looks like it accepted them anyway. There except we go here to plug accept. We're going blindly where no man ban has gone before. But what's cool about this is you know we're using git. So if something gets really mess messed up and just revert back. All right. Start the development server to test the integration. Okay. But then I kept yapping. So now it wants to do this. I wonder if it already did that. It must have. All right. So yeah, let's do it. npm rundev, baby. Okay, well, it ran. That's good. Let's open that up locally. It doesn't look like anything's loading. The site is not loading. Let's try that again. It loaded. Great. Go to the blog. All right. So, let's go back and check. Okay. Private versus public. Seven key signs of an authentic monostory classroom. Um, I don't see anything. These were there already. So now we say I'm not seeing the fetched blog posts, but I am seeing the original three. Let me help debug this. So now it's just adding some console logging. We're going to run that again. Okay, so my API key very, it wasn't the right name. I put SEO.AI, it was SEOAPI key. So that's probably going to do it. I hope. Let's refresh the blog page. No, it didn't do it. Okay, so it wants me to open your browser's developer console. F12 or right click, inspect console. Inspect. And we're here in the console down here. Let's refresh it. All right. So, lots going on here. I'm going to take a screenshot and I'm going to pop it in here. Say this is what's going on. And then it's clawed so it can read the image. Of course, it's a cross origin resource sharing error. SEO three book is blocking request. Oh, from local host. Oh, so I'm running this on a local host and that apparently is why it's not working. So that's a good reason for us to just go on to the next part. So this is our local host server. We're about to push it to the real server. Let's jump into what is Netlefi. Every time there's a new get push command with new changes, you can actually see it's going to build the new site. It'll let you do everything you need to. It'll even let you put your environmental variables. So, it now that we're doing this SEO.AI, I have to add a new environmental variable because what happens inside of git repos, which might not be in this one yet, but we have a git ignore file. And git ignore says, "Hey, don't send these files to the cloud because there's private information, which means you have to have this.n file alone on your computer in the repo that's ignored by git and then it's alone again on the internet." And the reason it's a file is so you can't access it through the you can't type in monosurfind.com/.n. It doesn't work. So that's why you want these sensitive variables. But in the case of Netlefi, we're not managing the server. It's the service doing that for us. So we don't have access to the end file and things like that. So that's why we add it in here in the menu. So we go new environment variable. Put that there. And I copy and paste that API key. Okay. And I've added the API key there with V SEO bot. Done. So here I am. We've got all this new blog stuff. What we're going to do now is close the active dev. We're going to stage these changes. Get commit. add SEObot API. Okay. And see how much it added. So look, 35 files changed, 6679 insertions, 68 deletions. So you can see everything going on in there. We're just trusting that it's all good. When we ran it locally, it was pretty good. It just couldn't pull the API because it was from local host. So now let's get push this. And I enter in my passphrase. Boom. All right. So you can see it's got all this going. We found five vulnerabilities. Um, I'm pretty sure we have those same ones when we run it locally. But now you'll see if I go back here to deploys on Netlefi and Monos. See, it's starting up a new one. Addobot API was the name of my last commit. If we go to GitHub here, my GitHub repo is private because there's data on there I don't want everyone to see. Uh, so you can use GitHub to make your websites private as well. I would recommend doing that in enough cases, I guess. Um, but here we go. And we can just see 1 minute ago there was uh a new commit. So we're seeing everything that's been happening and you can track these changes deploys. It's still building should be done any minute now. This is a good moment to share with you how you can see on the free account you get 300 build minutes. That's how long you use their server takes to build your website. You get 300 a month. So that's what that So if we get 30 seconds 30 seconds. So each time I make a change that I push it's it's 30 seconds of my credit. It's a pretty good deal to be honest. And as you get deeper and deeper into building websites in this manner, uh, Netifi is a really cool service. So once again, you're sacrificing some control and sovereignty like you don't have access to the server, but in a lot of cases like deploying node projects online can be we did that for my DAO a few years ago. We made like a treasury project, an NFT project, and we deployed it all. We had to have an extra server to manage the changes and it was just really a lot of work. So Nellifi is a great service. All right, so we've pushed it. So let's go back. This is This is the local host. Now, let's go to the full one. So, now we're at monostoryfind.com. Let's check the blog. Still not seeing it. Not seeing anything. So, that's when we go back to cursor. Oh, it looks like there was uh uh-oh. So, I missed something there. Apparently, I missed something. Oh, and we got to install the P. Oh, a lot happened that I didn't do. And now it looks like it was trying to fix it for local host. Anyway, user aborted requests. We installed that. I don't know. Let's just see if anything's happening differently right now. So now we're at localhost again. We go to blog. Nothing. And we're going to inspect. All right. Base fetch failed. Server responded with a 404. So I copy this image. Taking this copy and paste. I'm I'm I'm I'm just screenshotting it. Getting these errors in console. So it's still building all this from the perspective of the local host. Yeah. 404 not found. Wait. Access to fetch from or hood block block by course. Error fetching base type error. I think what we'll do. All right. So, we're just going to accept all that. At this point, I don't know what's going on anymore. And I might actually just start over. So, this is a good time to explain. We've gone too far. Okay. I don't care for it to make a proxy so we can load it from local host. I really don't care that much. I'm gonna stop everything going on. My internet is super slow today, which is kind of annoying. So, we've got all these errors. It went way too far in the other direction. We've learned some things. This is where we're like, "Okay, cursor, let's just start over." And to be honest, it's not going to take much to start over. So, we here we have this old commit. This is the last commit we made before SEO API. So, I'm just going to copy that commit ID there. And then I'm going to write get reset hard and then paste that commit name. And basically that's just saying, "Hey, reset to this to this one when those were the changes because we're too far now like with all this SEO stuff." Okay, so now we're back. Okay, we're back. And that one now you can see is detached. We're back here. Okay, so we're starting over here. We've just reverted back to where we were before and we have our docs folder, the SEO.xjs. And so what I'm going to do is I'm going to drag that into the agent. I'm going to say let's integrate the SEO bot API into our project. The API key is insobot API key. The API key is in there. Let's integrate the SEO bot project into our project to dynamically fetch new blog posts. um the API. Um and let's also say keep the original three blog posts as the very first posts. We can say static blog posts. All right. Now, let's give it another shot. And instead of deploying locally, we're just going to deploy straight through Netlefi to our domain name so we can avoid this whole proxy thing localhost issue with the SEO bot API. All right. Well, this is an interesting situation because it thinks in the chat history, it doesn't know we reverted back. So, let's just see what happens here. All right. First, we're just going to mpm rundev. It's running. Let's see what happens in here at the blog. Inspect. Let's refresh it. React router. Remove. Remove. Not sure. Don't have any errors in there. So, let's just um get commit. We're going to stage changes. Get commit message SEO bot version two. And if that doesn't do it, we're just going to have to kind of start over again. All right. And now we go back to net netlefi. It's new. We're going to see it starting up. It's going to be building. Pretty cool, right? I mean like you know if you're not really like a developer server engineer architect type person like it's this it's pretty cool. All right it's built. So I'm leaving the inspector open the console as we refresh this page. Okay this is from some web 3 plugin apparently. Whatever doesn't look like anything's wrong. Content script is ready. Okay. So we're not getting issues in the console but we're not seeing any any blog post. So here's where we go. No more issues in the console but no blog post displayed still. What should the URL be of the blog feed? This is where you just wonder is it like forgetting the basic like oh yeah fetch it all but then display them too. That's sometimes how it is working with these things and it's just how it goes. Which is why we need to have an overarching general knowledge of how all this stuff needs to work. Now I don't know why it's saying we're using the demo. No, it's getting the SEO API key there. Oh, okay. It found the issue. Okay. Yeah, so I was right. This is hilarious. It just didn't change the import. It's using the static blog post component instead of fetch blog post. Uh it's importing the static blog post instead of the dynamic fetch blog post from the API. So once again, silly implementation problem. So, we're going to add that get commit mix um function SEO boti. And the reason we do these commit messages is just so we have an idea of where we were, which is like if you're renaming a file version two, version three again, like it just doesn't work um for long big projects like this. So when you put the commit like exactly what you worked on, then if you have to go back and fix something, you can not only like revert back to that commit, but you can find little things that did work and then you messed it up later, but other things work and you don't want to lose that, but you don't want to lose that. So you can find what worked and you can like bring it back into your code. And that's where like you can become a really advanced git user, which I am not. Okay, so we've pushed a new commit. Let's go over to Netlifi. It's building. And as you see here, fix function SEO bot API. Now, I don't know what it did with that whole demo API thing. I hope doesn't mess anything up. Okay, it's built. So, we're on the blog post. Let's refresh it again. Moment of truth, ladies and gentlemen. Nothing. Uh, unable to fetch. Blocked by the cores present. All right. So, now from the console, we paste that in. And I have a feeling that has to do with the API key. Let's just do ask this time. What h this is the console error log when running on the live server. And hopefully we get something using no cores. Okay, so it looked like it thought it was going to do this. This is interesting. And then it realized, wait a minute, using no cores mode has limitations. Oh, so it still wants to create a proxy server. That's interesting. What I wonder is why do the documents not say how to do this? Just install all this. Oh, so it wants Oh, it wants you to use the demo key. Oh, for local development. Okay, so why don't we do that too? So we can just run this locally. That would be great, right? So there's a netifi thing going on here. Where is it? There it is. Netifi functions. Great. So now we make a new folder in there. SEO proxy.ts. ts and then we add that there file and update the SEO bot client to use the proxy. So now we got to find our SEO bot client which is probably here. I don't know what this is going to do exactly. All right. and then building SEO bot API key on netlifi the key is called vit seobot API key all right so I'm telling it that on netlefi in my build config I'm already using this v seo bot so back here it's going to use that now now for for local deployments ensure we use SEO API key. Actually, let's say this instead of the SEO API key. Okay, so I hope this works here. I'm basically saying use the bottom one or local deployments, use the top one for Netifi deployments. I'm kind of breaking my own rules here, solving one problem at a time. But I really don't want to keep having to deploy this and use the build minutes until we've get got it solved. And then like I said, I in the docs I finally realized that they give you a demo API key to use for local deployment. So I really should have um read that first. That's done. That's done. Okay. So let's do this. npm rundev. Let's open that up. Log. Still nothing. Right now, we're going to give it that. Go back to agent here. This is what went wrong in uh the browser console. Well, we already have that folder. Let's make it another file. I hope we're not going too deep again, but let's see what happens. This is kind of what happens working with APIs sometimes. Um I mean, even if you know what you're doing, which I obviously don't. I'm using an AI uh browser. I'm using an AI I'm using AI software to do it. But even when you know what you're doing, it's a little comp complex. All right. So, let's see if that works. Okay. Then we have to install. Okay. So, um let's npm rundev. Oh, it's still not done. Hang on. Okay. Got it. Okay. So, yeah, it did have to get kind of complicated saying, "Hey, if you're running on localhost, which is this port 5173, then make sure you use a different one." All right, now we're installing Netifi command line interface. And I'll tell you what, I sure hope it works after this cuz I do intend to edit this video and it's going to be a lot of work. All right, we've got all this in there. MPM rundev. Still nothing. still not working. It's wanting me to run the Netlefi server locally. This is just getting more and more annoying. So, I'm forgetting that. And I'm going to do get add get commit m api fix get push. I do have hope that it's going to work online because of that lo that API key thing. So hopefully this will all be good. I don't know why this is taking so long. Okay, so it's published. Here we are. We're leaving the console open. Let's see see how it goes. Oh, it's working. API post received zero. So something's definitely working. It's not finding our posts. So now I copy and paste that into there from the live server. API connection is working, but we're not pulling any posts. There should be at least two posts. Getting closer, everyone. We're getting closer. So, it's reading the documentation to solve this, which is pretty cool. Okay, so it's giving us something for the proxy, whatever. Let's just ask again on the blog display page. Are we using the correct function to display both the static post and the API fetch post? Although I guess that doesn't matter yet. Okay. So, um let's do mpm rundev again. Let's see what this is looking like on the dev server. Log inspect. Yeah, the fetch isn't working. That's a bummer. So, we got to just keep doing these deploys. Get add get commit. Um, more SEO by API login. Get push. Okay, it's built monostoryfind.com/blog. Nothing. Total post three. Fetch posts three. It says it fetched three posts. So, it's just one thing after another. Sometimes you want to give up, especially when you're not seeing any actual errors. But this is this is web development. This is just what software development is with or without AI. Because when you're working with machines and networking them together to do things, they're working on another level than our human minds. And you can always figure it out. You just got to keep working towards it. Content scripts initializing. It's running. It's going. Okay. So now at least we have some errors, right? Well, this is good. It seems to have found something. The other thing is like this is published. Oh, so the last thing we need to do here is make sure that these posts are published. Okay, so we're fetching posts now finally. So this is silly but the error was they weren't published on SEO bot pro. Um I had auto publish there but I think because I enabled that after these were written they weren't autopublished. So I publish them and I press sync and suddenly it all works. So but I'm getting errors um minified react error. So what we can do here is just copy and paste that. And now we're going to say, "Hey, it's finally working." But what are these errors? So now it's saying something about tags. So it's looking like it's all just about the mapping. So if I were to do this again, I would make sure everything's mapping correctly because this would have been a lot easier if I didn't have a blog yet. But because I already had a blog, we're going through a lot of problems. So, I'm showing it what the API is actually delivering. And that's probably what we should have done first. Just telling it everything that the API is going to give us. Real quick, just a reminder, if you're new to the command line, check out the 5day command line boot camp down below. It's 5 minutes for 5 days and you'll get a lot more confident. You can also just do it all in one day if you want. But if you're new to this and you want to start harnessing AIS to work for you and start building instead of being a passenger, a spectator, I recommend getting started with that email course. Check it out in the description. Back to it. All right, we're deployed. So, let's refresh the blog again. Boom. We did it. We did it, ladies and gentlemen. Okay, these are the new ones. And we got this weird read more thing, which we'll fix. And we just need to put it in the beginning, which shouldn't be a big problem either. Oh, and it's not loading the post. But the next thing I would say is, okay, it's loading the posts onto the feed now, but there are two problems. One, the feed entry is not linking to the actual blog post page. to um the dynamic post should be before the static posts. The static post should be last. So now we'll just find final touches, right? And from here I should hope you can figure this out. I'm going to finish it. Oh, it did work this time. Nope. Read more. Yeah, the read more button is not working. That's okay. Yeah. So once again, it's just step by step. It's not going to do all the steps at once, and that's okay. This just goes back to the the main rule number one is solve one problem at a time. Um, APIs can be more complicated than than we think. Oh, just connect to that and get it. But as we're seeing, TypeScript to Nex.js or whatever is going on, markdown to JSON, there's always something. It's all possible, but we need to make sure we're taking it step by step. So let's uh do what it says here. Okay, great. Um that dynamic post not here before. Click on post to read more. Okay, also remove the read more text and make sure the image and the title of the blog post both link to the blog page post, the blog post page. All right. So, I think that's it. I think we should be good by now. Fix blog feed display. Push. The last thing I'll do, assuming this works, is I got to make sure that the blog site map is either merged to my main site map or it's added to Google Search Console. Again, not my biggest concern for this exact video, but it's the same process. I'm going to go to the GitHub repo, which we really have right in here. Where's the docs? And we just go to the readme, and we see sitemap configuration. So, literally, I'll copy this. I'm going to send that to the chat. Now, merge the blog sitemap XML to our main sitemap.xml. I'm going to not send that until this is done. We confirm that this problem is solved. All right, we got the new ones there. They're all linked looking good and the dynamically fetched posts seem to link to log slug as they should. However, on click nothing happens and the user stays on the blog page. The links work appro fine for the static posts. Okay. So, we see here. Boom. It wasn't doing that right, I guess. All right. So, let's add So, I mean, obviously, this has taken a while, but considering I haven't done any real coding, an AI agent writing the SEO post, and it's just going to automatically update aside from a get commit and push twice a week on my end, like the headache's okay, right? You just have to know how to debug and know how to be able to check the browser consoles, be able to check the the error logs when you're running locally, etc. And if you can just stay on top of all that, you can eventually diagnose whatever it is and fix it with your AI co-pilot, and you're the captain, not the passenger. You're working with AI. You're doing it. And I really hope this works cuz I got other things I wanted to do today. Are we built yet? This is I don't know how long the edited video is going to be, but I'm at almost 2 hours. I'm at a minute an hour 58 55 seconds. Okay, we're published. Here we go. Nothing. Now, I wonder if I type in It might just be a routing problem. Seven key signs. If I go to these, go to the slug and I type that into the URL. I type that in. Does it load the post? No, it does not. Still not loading the page. I think it's a routing issue. When I enter into the browser, it just redirects to blog. Well, close though. Exactly. The client signed routing isn't handling dynamic routes. That makes sense if it's in the redirects in our neti folder. That would make a lot of sense. Whatever that folder is. No, let's just for fun go back to npm rundev and see what's happening locally. That's still not working there locally. Okay, let's try creating in a different way a redirects folder. Pretty sure we have that folder. Yeah, it's right here. This is already infy. Yeah. So, I thought it was a netifi routing thing, but I had that. So, it looks like, yeah, there's something going on that's not making the post from the original JSON. Now, I do wonder, it's too late now, but I do wonder what would have been like if I just said, take the data, convert it to JSON, add it to our JSON file for blog posts, and then be done. You know, just make a web hook instead. Instead, we did the API. It's taken me for a runaround. It's taken me 2 hours when it probably should have taken like half an hour. The truth be told, um, this is, I think, a smoother way, but all right. So, it just wants to do debug logging. The get post method is looking for an exact match. Add some debugging. All right. So, we go to the posts. Go to the console. It's taking the posts. I'm just going to expand every single thing here. The slug is there in the output. So, this agent is just helping me diagnose everything. All right. So, it wants to set an error message. I mean, that'll help. I check the network tab if there are any cores or other errors. All right. So, we're going to refresh this network. So, I think I found the problem. Basically, whatever's happening between the API and the Nex.js JS website saying, "Okay, these are the available blog posts and these are their ids. They're slugs." But somewhere in the mix, we started using a different slug, the slug that we got from SEO API, which was this like the URL slug, private versus public mon schools. So, what we really need to do is it needs to pull that dynamically instead of that. That should just be the URL slug. So it sees the issues. The agent sees the issue. The base data we're getting from the API contains post with ids as slugs rather than the human readable title slugs. We need to modify our code to handle this mismatch. Okay, so it made the changes. Yes. So convert the headline into URL slug. Okay, cool. I think this should do it. All right, so once again, I'm hoping this is going to be the last time. fix blog URL slugs push. Fingers crossed once again, my friends. And as soon as this is deployed, we will refresh it and then I will hopefully be on to my next thing that I got to do today. Here we go. Here we go. Hey. All right. So, it didn't fix all this, but that's okay. Okay, we'll figure that out next. We got it integrated. I mean, next up, I just got to say, hey, use the markdown instead. Convert it to JSON. But for now, this is a really good step. At least it's working. It's got the right slug up in the browser window. Looking good. Exciting. I mean, that's not looking good. Um, but it's got the images. All right. So, just to finish this up, cuz we're doing it great, it works now. But the blog post itself is a is text with HTML inside. We should be formatting the text or we should be pulling the markdown from the API and then formatting it display on our blog just like the original posts. This should be a pretty simple thing to solve. I mean, I guess you never know. I always make sure to let it know that I'm excited. Like, hey, it works now. How exciting. Okay. So, it sees that we can choose markdown instead of HTML. So, it's going to update the code there. All right. So, it made all these changes for markdown. And hopefully that fixed it. Make blog post markdown. All right. So, I'm pushing that. And the last thing I want to say is this is taking a minute each like it was 30 seconds before to deploy back when it was just the website with but now that it's got to tag the API to get new posts it's taking a minute. So if we go to the builds if I'm getting two posts a week then I'm going to have to commit and redeploy twice every week which is 2 minutes uh minimum. This isn't counting other features I add or other changes I make. So, I was at like I think half of this just about before this video, but because we're unable to really build locally or at least I didn't want to really figure that out. Maybe I should in the future, but because I wanted to do this video, I didn't have it figured out. Now, it's completed. Oh, that was only 30 seconds. That's good. But basically, we got to keep this in mind when we're we're developing and deploying is like sometimes we have constraints. So, the most optimal way to go about these problems is perhaps take care of them early on. All right. So, here we go. It used markdown. Boom. This is exactly what we looked like when we go all the way back to our original file that that uh SEO bot gave us. Seven key signs. Let's see. The slug is there. Seven key signs. Um these tables are there. That video, I don't see that YouTube video, which doesn't even really bother me because I wasn't sure I wanted to put a YouTube video anyway. So, block quotes. So, how did it handle these block quotes? Yeah, block quotes. This is amazing. Awesome. So, it I think my cursor and my project added the CTA there cuz as you'll see, I remember seeing a CTA right here. Find the best monos square tool. So, before number four, do we see it in there? Yeah, I actually don't see the CTA at all, but that's okay. um we can add a code in there or something that says like hey in the middle of every blog post insert basically insert this same CTA like start exploring. So there you have it how to bring an API in this case SEO API into your Nex.js or TypeScript project. This content I'm making is to help you learn how to do this. It's not necessarily like follow all the steps and you're going to get it. No, you need to have the the you need to have the mental duress. You need to be sovereign over this technology with the command line with APIs with Git in order to make this kind of thing happen with these AI co-pilots, with these AI agents. We can't rely on third party services for everything all the time cuz even if they exist, maybe they're expensive, maybe we'd rather just make our own. And essentially making our own is pretty cool and it can be fast. And look what we got done. So get to know the command line. Please check the 5day command line boot camp. I swear it'll be worth it. It's very basic, but it'll just get you started. What do you think? Are you building? What are you building? What do you need help with? Let me know in the comments. If you liked this video, thanks for leaving a like. I'll see you the next video.


















SEObot is an AI-powered SEO tool that automates tasks like keyword research, content creation, and optimization. Here's how it works:
Key Features:
Automated Keyword Research: SEObot uses AI to analyze your website and audience behavior to identify high-volume, low-competition keywords in real-time.
Content Creation: SEObot writes structured, Google-friendly blog posts in 50+ languages, optimized for keywords and designed to improve search rankings.
Internal Linking: SEObot simplifies internal linking to improve site navigation and search rankings.
Integration with CMS Platforms: SEObot works with popular CMS platforms like WordPress, Shopify, Webflow, and more.
How it Works:
Onboarding: You enter your website URL and other relevant information into SEObot.
Keyword Research: SEObot analyzes your website and audience behavior to identify high-volume, low-competition keywords.
Content Creation: SEObot creates optimized blog posts based on the keywords and topics you've identified.
Optimization: SEObot optimizes your content with SEO-friendly elements like short paragraphs, optimized image alt text, and proper HTML heading structure.
Publication: SEObot publishes your optimized content to your CMS platform.
Tracking: SEObot tracks your content's performance and provides insights to improve results.
Benefits:
Saves time and effort on SEO tasks
Improves search rankings and organic traffic
Increases clicks and conversions
Supports 50+ languages
Integrates with popular CMS platforms
Overall, SEObot is designed to make SEO easier and more efficient for busy founders and small business owners. By automating tasks like keyword research, content creation, and optimization, SEObot helps you grow your organic traffic effortlessly.
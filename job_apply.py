#---------- Data Gathering---------

f = open("user_config.txt", "r", encoding="utf-8")
f_lines = f.readlines()
f.close()

# Helper to safely get config values
def get_config(index):
    try:
        if index < len(f_lines):
            return f_lines[index].split('\t:')[-1].strip()
    except:
        pass
    return ""

API_KEY           = get_config(0)
USER_ID           = get_config(1)
PASSWORD          = get_config(2)
ROLES             = get_config(3)
INPUT_RESUME_PATH = get_config(4)
YEARS             = get_config(5)
MONTHS            = get_config(6)
LINKS             = get_config(7)
JOB_MODE          = get_config(8) or "Fresher" # Default to Fresher

# AI Imports
import base64
import json
import requests
import os
import time
import random
import sys

# Force UTF-8 encoding for Windows console to prevent emoji crashes
try:
    sys.stdout.reconfigure(encoding='utf-8')
except: pass

#--------- Imports and setup-----------
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

# Stealth User Agent
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]
options = webdriver.ChromeOptions()
options.add_argument(f"user-agent={random.choice(user_agents)}")
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

try:
    if 'driver' in locals():
        driver.quit()
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service,options=options)
except:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service,options=options)

driver.maximize_window()
time.sleep(2)

import csv
from datetime import datetime

LOG_FILE = "applied_jobs.csv"

# Initialize CSV log if it doesn't exist
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Job Title", "Status"])

print("""
\033[1;34m--------------------------------------------------
\033[1;36m           STARK LINKEDIN JOB APPLICANT BOT             
\033[1;34m--------------------------------------------------\033[0m
""")

#----------------- Core Functions (Perfected) -------------

def click_element_safe(element):
    """Safely clicks an element, using a React-safe MouseEvent dispatcher as fallback."""
    try:
        # 1. Standard Click
        element.click()
        return True
    except:
        try:
            # 2. React-Safe JS Event Dispatcher (Highly reliable for LinkedIn)
            driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles:true, cancelable: true}));", element)
            return True
        except:
            try:
                # 3. Action Chains
                try: driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                except: pass
                time.sleep(0.2)
                ActionChains(driver).move_to_element(element).click().perform()
                return True
            except:
                try:
                    # 4. Standard JS Click
                    driver.execute_script("arguments[0].click();", element)
                    return True
                except:
                    try:
                        # 5. Keyboard Enter (Final fallback)
                        element.send_keys(Keys.ENTER)
                        return True
                    except:
                        return False

def get_easy_apply_button():
    """Finds the Easy Apply button on the current job details."""
    selectors = [
        "//button[contains(@class, 'jobs-apply-button')]",
        "//button[contains(@class, 'artdeco-button--primary') and contains(., 'Apply')]",
        "//button[span[contains(text(), 'Easy Apply')]]",
        "//button[span[contains(text(), 'Apply')]]",
        "//button[contains(., 'Easy Apply')]",
        "//button[contains(., 'Apply')]",
        "//div[contains(@class, 'jobs-apply-button')]//button"
    ]
    
    for selector in selectors:
        try:
            buttons = driver.find_elements(By.XPATH, selector)
            for btn in buttons:
                text = btn.text.strip()
                # Check for "Easy Apply" or "Apply" (LinkedIn icon 'in' might be present)
                if ("Apply" in text or "Easy Apply" in text) and btn.is_displayed() and btn.is_enabled():
                    return btn
        except:
            continue
    return None

# Labels that should NEVER be clicked — always skip these
_BLOCKED_BTN_LABELS = {"save", "save application", "save draft", "save for later"}

def find_primary_button(labels):
    """Finds a button by a list of possible labels, ensuring it is visible and clickable.
    NEVER returns a 'Save' button — those are always blocked.
    """
    for label in labels:
        selectors = [
            f"//div[contains(@class,'artdeco-modal')]//button[@aria-label='{label}']",
            f"//div[contains(@class,'artdeco-modal')]//button[normalize-space()='{label}']",
            f"//div[contains(@class,'artdeco-modal')]//button[span[normalize-space()='{label}']]",
            f"//div[contains(@class,'artdeco-modal')]//button[contains(normalize-space(), '{label}')]",
            f"//button[@aria-label='{label}']",
            f"//button[normalize-space()='{label}']",
            f"//button[span[normalize-space()='{label}']]",
            f"//button[contains(normalize-space(), '{label}')]",
        ]
        for sel in selectors:
            try:
                btns = driver.find_elements(By.XPATH, sel)
                for btn in btns:
                    btn_text = btn.text.strip().lower()
                    if btn.is_displayed() and btn.is_enabled() and btn_text not in _BLOCKED_BTN_LABELS:
                        return btn
            except: pass

    # Fallback: Generic Primary Button in Modal — strictly exclude any Save variant
    try:
        btns = driver.find_elements(By.XPATH, "//div[contains(@class, 'artdeco-modal')]//button[contains(@class, 'artdeco-button--primary')]")
        for btn in btns:
            btn_text = btn.text.strip().lower()
            if btn.is_displayed() and btn.is_enabled() and btn_text not in _BLOCKED_BTN_LABELS and btn_text != "":
                return btn
    except: pass

    return None

def close_active_modal():
    """Aggressively attempts to close any active modal. Always discards to move to next job."""
    print("   >> Cleanup: Closing modal (Discarding any drafts)...")
    
    start_time = time.time()
    while time.time() - start_time < 10:
        if not driver.find_elements(By.CLASS_NAME, "artdeco-modal"):
            return 
            
        # 1. 'Done' button (Post-Apply success)
        done_btns = driver.find_elements(By.XPATH, "//button[span[normalize-space()='Done']]")
        if done_btns:
            click_element_safe(done_btns[0])
            time.sleep(1)
            continue
            
        # 2. 'Dismiss' / X button
        close_selectors = [
            "//button[@aria-label='Dismiss']",
            "//button[contains(@class, 'artdeco-modal__dismiss')]",
            "//button[@data-test-modal-close-btn]",
            "//li-icon[@type='cancel-icon']/.."
        ]
        
        for sel in close_selectors:
            try:
                btns = driver.find_elements(By.XPATH, sel)
                for btn in btns:
                    if btn.is_displayed():
                        click_element_safe(btn)
                        time.sleep(0.5)
            except: pass
        
        # 3. Handle 'Save this application?' or 'Discard' confirmation
        discard_selectors = [
            "//button[span[normalize-space()='Discard']]",
            "//button[contains(., 'Discard')]",
            "//button[@data-control-name='discard_application_confirm_btn']",
            "//button[contains(@class, 'artdeco-button--primary') and span[text()='Discard']]",
            "//button[span[text()='No, discard']]"
        ]
        
        for sel in discard_selectors:
            try:
                btns = driver.find_elements(By.XPATH, sel)
                for btn in btns:
                    if btn.is_displayed():
                        click_element_safe(btn)
                        time.sleep(1)
            except: pass

        # 4. Escape Key
        if driver.find_elements(By.CLASS_NAME, "artdeco-modal"):
            try:
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                time.sleep(0.5)
            except: pass

    # Last ditch: Refresh
    if driver.find_elements(By.CLASS_NAME, "artdeco-modal"):
         print("   !! Modal stuck. Refreshing page.")
         driver.refresh()
         time.sleep(5)

def check_for_resume_requirement():
    """Checks if a resume upload is visibly blocking us."""
    if not INPUT_RESUME_PATH or not os.path.exists(INPUT_RESUME_PATH):
        # Only block if there's an error message related to file/resume
        try:
            errors = driver.find_elements(By.CLASS_NAME, "artdeco-inline-feedback__message")
            for err in errors:
                if "resume" in err.text.lower() or "file" in err.text.lower():
                    print("   !! Job requires Resume Upload and application is blocked.")
                    return True
        except:
            pass
    return False

#----------------- AI & Form Filling -------------

def find_element_by_label_fuzzy(label_text, modal):
    """ Tries to find an input element by fuzzy matching the label text. """
    try:
        # 1. Exact Label Match
        labels = modal.find_elements(By.TAG_NAME, "label")
        for l in labels:
            if label_text.lower() in l.text.lower():
                 for_id = l.get_attribute("for")
                 if for_id:
                     return driver.find_element(By.ID, for_id), l
        
        # 2. Aria-Label Match
        inputs = modal.find_elements(By.XPATH, "//input | //textarea | //select")
        for inp in inputs:
            aria = inp.get_attribute("aria-label")
            if aria and label_text.lower() in aria.lower():
                return inp, None
                
        # 3. Placeholder Match
        for inp in inputs:
            placeholder = inp.get_attribute("placeholder")
            if placeholder and label_text.lower() in placeholder.lower():
                return inp, None
                
        # 4. Fallback: Legend for radio groups
        legends = modal.find_elements(By.TAG_NAME, "legend")
        for leg in legends:
             if label_text.lower() in leg.text.lower():
                 fieldset = leg.find_element(By.XPATH, "./..")
                 return fieldset, leg
                 
    except:
        pass
    return None, None

def rule_based_fallback_filler():
    """Comprehensive rule-based filler for all common LinkedIn form fields."""
    try:
        modal = driver.find_element(By.CLASS_NAME, "artdeco-modal")

        # ---- Phone Number ----
        try:
            phones = modal.find_elements(By.XPATH,
                ".//input[contains(@id,'phone') or contains(@name,'phone') or contains(@aria-label,'phone')]"
            )
            for p in phones:
                if p.is_displayed() and not p.get_attribute("value"):
                    p.clear(); p.send_keys("7904797825")
        except: pass

        # ---- City / Location ----
        try:
            locs = modal.find_elements(By.XPATH,
                ".//input[contains(@id,'city') or contains(@name,'city') or contains(@aria-label,'city') or contains(@aria-label,'location')]"
            )
            for l in locs:
                if l.is_displayed():
                    l.clear(); l.send_keys("Chennai, India")
                    time.sleep(0.6)
                    l.send_keys(Keys.ARROW_DOWN); l.send_keys(Keys.ENTER)
        except: pass

        # ---- All numeric/text inputs by label heuristic ----
        try:
            for inp in modal.find_elements(By.TAG_NAME, "input"):
                itype = inp.get_attribute("type") or "text"
                if itype not in ["text", "number"]: continue
                if not inp.is_displayed(): continue
                existing = inp.get_attribute("value") or ""
                label_txt = ""
                try:
                    iid = inp.get_attribute("id")
                    if iid:
                        lbl = modal.find_element(By.XPATH, f".//label[@for='{iid}']")
                        label_txt = lbl.text.lower()
                except: pass
                if not label_txt:
                    label_txt = (inp.get_attribute("aria-label") or "").lower()
                if not label_txt:
                    label_txt = (inp.get_attribute("placeholder") or "").lower()

                if not existing:
                    if any(k in label_txt for k in ["year","experience","exp"]):
                        inp.send_keys("1")
                    elif any(k in label_txt for k in ["salary","ctc","package"]):
                        inp.send_keys("400000")
                    elif any(k in label_txt for k in ["notice","days"]):
                        inp.send_keys("0")
                    elif any(k in label_txt for k in ["gpa","cgpa","score","percentage"]):
                        inp.send_keys("8.0")
                    elif any(k in label_txt for k in ["name"]):
                        inp.send_keys("Barath")
        except: pass

        # ---- Select dropdowns ----
        try:
            from selenium.webdriver.support.ui import Select
            for sel_el in modal.find_elements(By.TAG_NAME, "select"):
                if not sel_el.is_displayed(): continue
                sel = Select(sel_el)
                opts = [o.text.lower() for o in sel.options]
                # Pick first non-blank option if nothing selected
                current = sel.first_selected_option.text.strip()
                if not current or current.lower() in ["", "select an option", "select", "--"]:
                    label_txt = (sel_el.get_attribute("aria-label") or "").lower()
                    if "country" in label_txt:
                        for o in sel.options:
                            if "india" in o.text.lower():
                                sel.select_by_visible_text(o.text); break
                    elif "gender" in label_txt:
                        for o in sel.options:
                            if "male" in o.text.lower() and "fe" not in o.text.lower():
                                sel.select_by_visible_text(o.text); break
                    else:
                        # Just pick index 1 (skip blank index 0)
                        if len(sel.options) > 1:
                            sel.select_by_index(1)
        except: pass

        # ---- Radio Buttons (expanded logic) ----
        try:
            for fs in modal.find_elements(By.TAG_NAME, "fieldset"):
                if not fs.is_displayed(): continue
                text = fs.text.lower()
                yes_labels = fs.find_elements(By.XPATH, ".//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'yes')]")
                no_labels  = fs.find_elements(By.XPATH, ".//label[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'no')]")

                # Already answered?
                checked = fs.find_elements(By.XPATH, ".//input[@type='radio'][@checked or @aria-checked='true']")
                if checked: continue

                if any(k in text for k in ["authorized","eligible","legal","citizen","clearance","willing","relocat","currently"]):
                    if yes_labels: click_element_safe(yes_labels[0])
                elif any(k in text for k in ["sponsor","visa","require sponsor"]):
                    if no_labels:  click_element_safe(no_labels[0])
                elif any(k in text for k in ["disability","veteran","gender","race","ethnicity"]):
                    # Try to pick 'Prefer not to disclose' or last option
                    all_labels = fs.find_elements(By.TAG_NAME, "label")
                    for al in reversed(all_labels):
                        if any(k in al.text.lower() for k in ["prefer","decline","not to","wish not"]):
                            click_element_safe(al); break
                    else:
                        if all_labels: click_element_safe(all_labels[-1])
                else:
                    if yes_labels: click_element_safe(yes_labels[0])
        except: pass

    except: pass

def _extract_form_fields_as_text(modal):
    """Extracts visible form fields from the modal as structured text for Gemini."""
    fields = []
    try:
        # Text / number inputs
        for inp in modal.find_elements(By.XPATH, ".//input[@type='text' or @type='number' or @type='tel' or @type='email'] | .//textarea"):
            if not inp.is_displayed(): continue
            iid = inp.get_attribute("id") or ""
            label_txt = ""
            if iid:
                try:
                    label_txt = modal.find_element(By.XPATH, f".//label[@for='{iid}']").text.strip()
                except: pass
            if not label_txt:
                label_txt = (inp.get_attribute("aria-label") or inp.get_attribute("placeholder") or "").strip()
            val = inp.get_attribute("value") or ""
            tag = inp.tag_name
            fields.append(f"FIELD | type:{tag} | label:{label_txt} | current_value:{val}")

        # Select dropdowns
        for sel in modal.find_elements(By.TAG_NAME, "select"):
            if not sel.is_displayed(): continue
            label_txt = (sel.get_attribute("aria-label") or "").strip()
            opts = [o.text.strip() for o in sel.find_elements(By.TAG_NAME, "option") if o.text.strip()]
            fields.append(f"FIELD | type:select | label:{label_txt} | options:{opts}")

        # Radio/checkbox fieldsets
        for fs in modal.find_elements(By.TAG_NAME, "fieldset"):
            if not fs.is_displayed(): continue
            try: legend = fs.find_element(By.TAG_NAME, "legend").text.strip()
            except: legend = ""
            opts = [l.text.strip() for l in fs.find_elements(By.TAG_NAME, "label") if l.text.strip()]
            fields.append(f"FIELD | type:radio | label:{legend} | options:{opts}")
    except: pass
    return "\n".join(fields)


def ai_solver():
    """Uses Gemini Flash to intelligently fill all form fields on the current modal."""

    # Always run rule-based first as fast baseline
    rule_based_fallback_filler()

    if not API_KEY:
        print("   [AI] No API key. Using rule-based only.")
        return False
    if not driver.find_elements(By.CLASS_NAME, "artdeco-modal"):
        return False

    print("   [AI] Gemini analyzing form...")
    try:
        modal = driver.find_elements(By.CLASS_NAME, "artdeco-modal")[0]

        # Scroll modal to top so screenshot captures all fields
        try:
            mb = modal.find_element(By.CLASS_NAME, "artdeco-modal__content")
            driver.execute_script("arguments[0].scrollTop = 0;", mb)
            time.sleep(0.3)
        except: pass

        # Take screenshot for visual context
        b64_image = base64.b64encode(modal.screenshot_as_png).decode('utf-8')

        # Also extract form fields as text (more reliable than image alone)
        form_text = _extract_form_fields_as_text(modal)

        exp_str = (
            f"{YEARS} years and {MONTHS} months"
            if (int(YEARS or 0) > 0 or int(MONTHS or 0) > 0)
            else "Fresher / Entry Level (0 years)"
        )

        prompt = f"""You are helping automate a LinkedIn Easy Apply form. Analyze the form screenshot AND the extracted fields below, then return answers for every visible field.

CANDIDATE PROFILE:
- Full Name: Barath
- Email: {USER_ID}
- Phone: 7904797825
- Role Applying For: {ROLES}
- Experience: {exp_str}
- Location: Chennai, Tamil Nadu, India
- Expected CTC / Salary: 4 LPA (400000 INR per annum)
- Notice Period: Immediate (0 days)
- Work Authorization: Authorized to work in India = YES
- Requires Visa Sponsorship: NO
- Willing to Relocate: YES
- Gender: Male
- Highest Education: Bachelor of Engineering (B.E.) - Computer Science
- Languages Known: English, Tamil
- LinkedIn Profile: Available
- Skills: Java, Python, SQL, Spring Boot, REST APIs

EXTRACTED FORM FIELDS:
{form_text}

RULES:
1. For "years of experience" fields → use 0 (fresher)
2. For salary/CTC numeric → use 400000
3. For notice period → use 0
4. For Yes/No authorization questions → answer Yes
5. For sponsorship questions → answer No
6. For "Select" dropdowns → pick the most appropriate option from the options list
7. For text fields asking about a skill → answer "Yes" or "1"
8. NEVER leave required fields empty
9. Return ONLY a valid JSON array. No explanation. No markdown.

OUTPUT FORMAT (JSON array):
[{{"label": "<field label>", "type": "<text|number|textarea|radio|dropdown|select|checkbox>", "answer": "<your answer>"}}]
"""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/png", "data": b64_image}}
                ]
            }],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048}
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        result = response.json()

        raw = result['candidates'][0]['content']['parts'][0]['text'].strip()
        # Strip markdown code fences if present
        if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:   raw = raw.split("```")[1].split("```")[0].strip()

        ai_data = json.loads(raw)
        if isinstance(ai_data, dict): ai_data = [ai_data]
        print(f"   [AI] Got {len(ai_data)} field answer(s) from Gemini.")

        from selenium.webdriver.support.ui import Select as SeleniumSelect

        for item in ai_data:
            answer    = str(item.get("answer", "")).strip()
            q_type    = item.get("type", "text").lower()
            label_txt = item.get("label", "").strip()
            if not answer or not label_txt: continue

            target, label_el = find_element_by_label_fuzzy(label_txt, modal)
            if not target and not label_el:
                print(f"      [AI] Could not locate field: '{label_txt}'")
                continue

            try:
                scroll_target = label_el if label_el else target
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", scroll_target)
                time.sleep(0.15)

                # ---- TEXT / NUMBER / TEXTAREA ----
                if q_type in ["text", "number", "numeric", "textarea", "tel", "email"]:
                    el = target
                    if not el:
                        label_el.click()
                        el = driver.switch_to.active_element
                    try:
                        el.clear()
                        driver.execute_script("arguments[0].value = '';", el)
                    except: pass
                    el.send_keys(answer)

                # ---- RADIO ----
                elif q_type == "radio":
                    ans_lower = answer.lower()
                    # Try inside the fieldset / parent context
                    parent = target if target else label_el
                    try:
                        fieldset = parent.find_element(By.XPATH, "ancestor-or-self::fieldset")
                    except:
                        fieldset = modal
                    clicked = False
                    for lbl in fieldset.find_elements(By.TAG_NAME, "label"):
                        if ans_lower in lbl.text.lower():
                            click_element_safe(lbl); clicked = True; break
                    if not clicked:
                        # Fallback: find radio input by value
                        for radio in fieldset.find_elements(By.XPATH, ".//input[@type='radio']"):
                            if ans_lower in (radio.get_attribute("value") or "").lower():
                                click_element_safe(radio); break

                # ---- SELECT DROPDOWN ----
                elif q_type in ["select", "dropdown"]:
                    if target and target.tag_name == "select":
                        sel = SeleniumSelect(target)
                        # Try matching by visible text
                        matched = False
                        for opt in sel.options:
                            if answer.lower() in opt.text.lower():
                                sel.select_by_visible_text(opt.text)
                                matched = True; break
                        if not matched and len(sel.options) > 1:
                            sel.select_by_index(1)
                    else:
                        # Custom dropdown (div-based)
                        el = target if target else label_el
                        click_element_safe(el)
                        time.sleep(0.4)
                        try:
                            opts = driver.find_elements(By.XPATH,
                                f"//div[contains(@class,'dropdown')]//li | //ul[contains(@class,'select')]//li")
                            for opt in opts:
                                if answer.lower() in opt.text.lower():
                                    click_element_safe(opt); break
                        except: pass

                # ---- CHECKBOX ----
                elif q_type == "checkbox":
                    cb = target
                    if not cb and label_el:
                        try: cb = label_el.find_element(By.XPATH, ".//input[@type='checkbox'] | preceding-sibling::input")
                        except: pass
                    if cb and not cb.is_selected():
                        click_element_safe(cb)

            except Exception as field_err:
                print(f"      [AI] Field fill error for '{label_txt}': {field_err}")
            time.sleep(0.1)

        return True

    except Exception as e:
        print(f"   [AI] Gemini API error: {e}")
        return False

#----------------- Main Flow -------------

def discard_save_popup():
    """HIGHEST PRIORITY: Immediately click Discard if the Save popup appears."""
    try:
        # Check for the Save popup dialog
        selectors = [
            "//button[normalize-space(.)='Discard']",
            "//button[span[normalize-space()='Discard']]",
            "//button[normalize-space(.)='No, discard']",
            "//button[@data-control-name='discard_application_confirm_btn']",
        ]
        for sel in selectors:
            btns = driver.find_elements(By.XPATH, sel)
            for btn in btns:
                if btn.is_displayed():
                    print("   >> DISCARD POPUP DETECTED - Clicking Discard now!")
                    # Use all 3 methods to ensure it is clicked
                    try: btn.click()
                    except:
                        try: driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles:true, cancelable: true}));", btn)
                        except: driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1.5)
                    return True
    except: pass
    return False

def force_click_button(btn):
    """Tries every possible method to click a button reliably on LinkedIn."""
    methods = [
        lambda: btn.click(),
        lambda: driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {view: window, bubbles:true, cancelable: true}));", btn),
        lambda: ActionChains(driver).move_to_element(btn).click().perform(),
        lambda: driver.execute_script("arguments[0].click();", btn),
        lambda: btn.send_keys(Keys.ENTER),
        lambda: btn.send_keys(Keys.SPACE),
    ]
    for method in methods:
        try:
            method()
            return True
        except: pass
    return False

def handle_application_flow():
    """Handles the wizard steps (Next -> Review -> Submit) one by one.
    - Runs AI form-fill on EVERY step before clicking Next.
    - NEVER clicks Save; always discards any save popup.
    - Shows clear step-by-step progress.
    """
    max_steps = 30
    step = 0
    stuck_count = 0

    while step < max_steps:
        step += 1
        time.sleep(2)
        print(f"   [STEP {step}] Checking application state...")

        # --- ALWAYS: Kill any Save popup first ---
        if discard_save_popup():
            time.sleep(1)
            continue

        # --- Check: Modal gone = submitted ---
        if not driver.find_elements(By.CLASS_NAME, "artdeco-modal"):
            print("   >> Modal closed. Application submitted!")
            return True

        # --- Check: Success text in modal ---
        try:
            modal_text = driver.find_element(By.CLASS_NAME, "artdeco-modal").text
            if any(x in modal_text.lower() for x in [
                "application was sent", "application submitted", "successfully applied", "your application was sent"
            ]):
                print("   [SUCCESS] Submission confirmed!")
                done_btns = driver.find_elements(By.XPATH,
                    "//button[span[normalize-space()='Done']] | //button[normalize-space()='Done']")
                for d in done_btns:
                    if d.is_displayed():
                        force_click_button(d)
                        time.sleep(1.5)
                        break
                return True
        except: pass

        # --- Dismiss floating toasts ---
        try:
            for t in driver.find_elements(By.XPATH, "//button[contains(@class,'artdeco-toast-item__dismiss')]"):
                if t.is_displayed():
                    try: t.click()
                    except: pass
        except: pass

        # --- Scroll modal content to bottom (reveals hidden buttons) ---
        try:
            modal_body = driver.find_element(By.CLASS_NAME, "artdeco-modal__content")
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", modal_body)
            time.sleep(0.5)
        except: pass

        # --- ALWAYS run AI to fill any visible form fields on this step ---
        print(f"   [AI] Filling form fields on step {step}...")
        ai_solver()
        time.sleep(1)

        # --- Check for validation errors after AI fill ---
        errors = driver.find_elements(By.CLASS_NAME, "artdeco-inline-feedback__message")
        if errors:
            print(f"   [WARNING] {len(errors)} validation error(s) remain after AI fill. Retrying...")
            stuck_count += 1
            time.sleep(2)
            if stuck_count > 4:
                print("   [ERROR] Cannot fix validation errors. Skipping job.")
                return False
            continue
        else:
            stuck_count = 0  # Reset stuck counter when no errors

        # --- Re-scroll to reveal buttons after filling ---
        try:
            modal_body = driver.find_element(By.CLASS_NAME, "artdeco-modal__content")
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", modal_body)
            time.sleep(0.5)
        except: pass

        # --- Kill Save popup one more time before clicking any button ---
        if discard_save_popup():
            time.sleep(1)
            continue

        # --- Find action buttons (Save is ALWAYS excluded in find_primary_button) ---
        submit_btn = find_primary_button(["Submit application", "Submit", "Send application"])
        review_btn = find_primary_button(["Review your application", "Review"])
        next_btn   = find_primary_button(["Continue to next step", "Next", "Continue"])

        if submit_btn:
            print("   >> [SUBMIT] Clicking Submit button...")
            try: driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
            except: pass
            time.sleep(0.5)
            force_click_button(submit_btn)
            print("   >> Submit clicked. Waiting 5s for confirmation...")
            time.sleep(5)
            discard_save_popup()  # In case submit triggers a save dialog
            continue  # Loop back to check success

        elif review_btn:
            print("   >> [REVIEW] Clicking Review button...")
            try: driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", review_btn)
            except: pass
            time.sleep(0.5)
            force_click_button(review_btn)
            time.sleep(2)
            continue

        elif next_btn:
            print(f"   >> [NEXT] Clicking Next on step {step}...")
            try: driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
            except: pass
            time.sleep(0.5)

            # Snapshot modal HTML length to detect if the step actually advanced
            try:
                modal_elem = driver.find_elements(By.CLASS_NAME, "artdeco-modal")[-1]
                prev_html_len = len(modal_elem.get_attribute('innerHTML'))
            except:
                prev_html_len = 0

            force_click_button(next_btn)
            time.sleep(3)

            discard_save_popup()  # Kill save popup immediately after Next

            # Verify step advanced
            try:
                modal_elem = driver.find_elements(By.CLASS_NAME, "artdeco-modal")[-1]
                curr_html_len = len(modal_elem.get_attribute('innerHTML'))
                if abs(curr_html_len - prev_html_len) < 50:
                    print("   ! Step did not advance after Next click.")
                    stuck_count += 1
                    if stuck_count > 5:
                        print("   [ERROR] Stuck on same step too long. Skipping job.")
                        return False
            except: pass
            continue

        else:
            print("   ? No Next/Review/Submit button found.")
            stuck_count += 1
            if stuck_count > 5:
                print("   [ERROR] Could not progress. Skipping job.")
                return False
            time.sleep(2)
            continue

    print("   [ERROR] Max steps reached without submitting.")
    return False

def process_page_jobs():
    """Processes all jobs on the current page ONE BY ONE.
    - Displays each job clearly before processing.
    - NEVER clicks Save — always discards.
    - Applies via Easy Apply only.
    """
    # Try different card selectors LinkedIn uses
    base_selector = "job-card-container"
    if not driver.find_elements(By.CLASS_NAME, base_selector):
        base_selector = "jobs-search-results__list-item"

    initial_cards = driver.find_elements(By.CLASS_NAME, base_selector)
    count_jobs = len(initial_cards)
    print(f"\n>> Found {count_jobs} job(s) on this page.")
    results = {"applied": 0, "failed": 0, "skipped": 0, "already_applied": 0}

    for i in range(count_jobs):
        print(f"\n\033[1;34m{'='*55}\033[0m")
        print(f"\033[1;34m  PROCESSING JOB {i+1} of {count_jobs}\033[0m")
        print(f"\033[1;34m{'='*55}\033[0m")

        try:
            # --- Step 1: Clean up any leftover modal from previous job ---
            # Always discard, NEVER save
            if driver.find_elements(By.CLASS_NAME, "artdeco-modal"):
                print("   > Leftover modal detected. Discarding...")
                discard_save_popup()
                time.sleep(0.5)
                # Try ESC if still open
                if driver.find_elements(By.CLASS_NAME, "artdeco-modal"):
                    try:
                        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                        time.sleep(1)
                    except: pass
                # Final discard attempt
                discard_save_popup()
                time.sleep(0.5)

            # --- Step 2: Re-fetch job cards (DOM may have changed) ---
            current_cards = driver.find_elements(By.CLASS_NAME, base_selector)
            if i >= len(current_cards):
                print(f"   > Job {i+1} no longer in DOM. Stopping page.")
                break
            card = current_cards[i]

            # --- Step 3: Scroll job card into view ---
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", card)
            time.sleep(1.5)

            # --- Step 4: Get job title ---
            try:
                title_elem = card.find_element(By.CLASS_NAME, "job-card-list__title")
                title = title_elem.text.strip()
            except:
                try:
                    title = card.find_element(By.TAG_NAME, "a").text.strip() or f"Job #{i+1}"
                except:
                    title = f"Job #{i+1}"

            print(f"\n\033[1;36m  Title : {title}\033[0m")

            # --- Step 5: Skip if already applied (card level check) ---
            try:
                card_text = card.text.lower()
                if "applied" in card_text and "easy apply" not in card_text:
                    print("   >> SKIP: Already applied (card badge).")
                    results["already_applied"] += 1
                    continue
            except: pass

            # --- Step 6: Click job card to load details ---
            print("   > Clicking job to load details...")
            if not click_element_safe(card):
                print("   >> FAIL: Could not click job card.")
                results["failed"] += 1
                continue
            time.sleep(2.5)

            # --- Step 7: Skip if already applied (details pane check) ---
            try:
                details_text = driver.find_element(By.CLASS_NAME, "jobs-search__job-details").text.lower()
                if "applied" in details_text and "easy apply" not in details_text:
                    print("   >> SKIP: Already applied (details pane).")
                    results["already_applied"] += 1
                    continue
            except: pass

            # --- Step 8: Find Easy Apply button ---
            apply_btn = get_easy_apply_button()
            if not apply_btn:
                print("   >> SKIP: No Easy Apply button found.")
                results["skipped"] += 1
                continue

            # --- Step 9: Click Easy Apply and run application wizard ---
            print("   > Clicking Easy Apply...")
            click_element_safe(apply_btn)
            time.sleep(3)

            # Kill any Save popup that might appear immediately
            discard_save_popup()

            print("   > Running application wizard (Next -> ... -> Submit)...")
            success = handle_application_flow()

            if success:
                print(f"   \033[1;32m>> SUCCESS: Applied to '{title}'!\033[0m")
                results["applied"] += 1
                with open(LOG_FILE, 'a', newline='', encoding='utf-8') as lf:
                    writer = csv.writer(lf)
                    writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), title, "Applied"])
            else:
                print(f"   \033[1;31m>> FAILED: Could not complete application for '{title}'.\033[0m")
                results["failed"] += 1
                with open(LOG_FILE, 'a', newline='', encoding='utf-8') as lf:
                    writer = csv.writer(lf)
                    writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), title, "Failed"])

            # Always clean up modal after each job (discard, never save)
            close_active_modal()
            time.sleep(1.5)

        except Exception as e:
            print(f"   \033[1;31m>> ERROR on job {i+1}: {e}\033[0m")
            results["failed"] += 1
            close_active_modal()

        # Show running totals after each job
        print(f"   \033[1;33m[TOTALS SO FAR] Applied:{results['applied']} | Skipped:{results['skipped']} | Failed:{results['failed']} | AlreadyApplied:{results['already_applied']}\033[0m")

    return results

#------------- Login ---------------
print("\033[1;33m>> Starting LinkedIn Login Process...\033[0m")
driver.get("https://www.linkedin.com/login")
time.sleep(3)

try:
    if driver.find_elements(By.ID, "username"):
        print("   > Entering credentials...")
        driver.find_element(By.ID, "username").send_keys(USER_ID)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.ID, "password").send_keys(Keys.ENTER)
        
        # Wait for home page to load
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "global-nav")))
            print("   >> Successfully reached LinkedIn home.")
        except:
            print("   ⚠️ Login taking longer than expected...")
        time.sleep(2)
    
    # Check for login errors
    if "login-submit" in driver.current_url or driver.find_elements(By.ID, "error-for-password"):
        print("\033[1;31m   [ERROR] Login failed! Please check your username/password in user_config.txt\033[0m")
        input("Press Enter after you have manually logged in to continue...")

    # Captcha check
    if "checkpoint" in driver.current_url or driver.find_elements(By.CLASS_NAME, "captcha-container"):
        print("\n\033[1;31m[WARNING] SECURITY CHECK DETECTED!\033[0m")
        print("\033[1;36m>> Please solve the CAPTCHA in the browser window.\033[0m")
        while "checkpoint" in driver.current_url or driver.find_elements(By.CLASS_NAME, "captcha-container"):
            time.sleep(2)
        print("\033[1;32m[SUCCESS] Security check passed. Continuing automation...\033[0m")
    
    print("\033[1;32m>> Login check complete.\033[0m")
except Exception as e:
    print(f"\033[1;31m>> Login Error: {e}\033[0m")

#------------- Navigation ---------------
roles_list = [r.strip() for r in ROLES.split(',')]
total_applied = 0
applied_jobs_log = []

try:
    for role in roles_list:
        if not role: continue
        print(f"\n\033[1;35m==================================================")
        print(f"   TARGET ROLE: {role.upper()}")
        print(f"==================================================\033[0m")
        
        encoded_role = requests.utils.quote(role)
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_role}&f_AL=true&sortBy=DD"
        
        if JOB_MODE == "Fresher":
            print("\033[1;36m>> Mode: Fresher (Filtering for Intern/Entry level)\033[0m")
            search_url += "&f_E=1%2C2"
        
        driver.get(search_url)
        time.sleep(5)

        for page in range(5):
            print(f"\n\033[1;34m--- PAGE {page + 1} ---\033[0m")
            page_results = process_page_jobs()
            total_applied += page_results["applied"]
            
            print(f"\n   \033[1;34m[PAGE SUMMARY]\033[0m")
            print(f"   Applied: {page_results['applied']} | Already Applied: {page_results['already_applied']} | Failed: {page_results['failed']}")
            
            try:
                # Scroll to find next page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                next_page_btn = driver.find_element(By.XPATH, f"//button[@aria-label='Page {page+2}']")
                print(f"   >> Moving to Page {page+2}...")
                click_element_safe(next_page_btn)
                time.sleep(5)
            except:
                print("\033[1;33m>> Reached end of results for this role.\033[0m")
                break
finally:
    print(f"\n\033[1;32m==================================================")
    print(f"   WORK COMPLETED! SUCCESSFUL APPLICATIONS: {total_applied}")
    print(f"==================================================\033[0m")
    input("\nPress Enter to close the browser...")
    driver.quit()

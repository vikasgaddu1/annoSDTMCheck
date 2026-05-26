# Validation Settings - Quick Start Guide

## What's New?

You can now customize:
1. **Author Name** - Applied to all PDF annotations during standardization
2. **Bookmark Labels** - Names for the two main bookmark sections in PDFs

## How to Use

### Step 1: Open the Application
```bash
py -m sdtm_checker
```

### Step 2: Configure Settings
1. Click on the **"Configuration"** tab (top of window)
2. Click on the **"Validation Settings"** sub-tab
3. Find the configurable fields:
   - **Generic Author Name** - Author applied to all annotations
   - **Form Bookmark Label** - Name for form-based bookmarks section
   - **SDTM Bookmark Label** - Name for domain-based bookmarks section
4. Type your desired values

### Step 3: Save Your Settings
- Click **"Save Configuration As..."** button (bottom of window)
- Choose where to save your config file
- Or just use the default config (saves automatically)

### Step 4: Standardize Your PDF
1. Go to **"File Paths"** tab and select your CRF PDF
2. Click **"Standardize Annotations"** button (bottom of window)
3. Choose output location
4. Confirm - you'll see YOUR custom settings in the confirmation dialog!

## Examples

### Example 1: Personal/Team Configuration
**Settings:**
- Generic Author Name: `Jane Smith`
- Form Bookmark Label: `Forms`
- SDTM Bookmark Label: `Domains`

**Result:** 
- All annotations show "Jane Smith" as author
- Bookmarks organized under "Forms" and "Domains"

### Example 2: Organization Configuration
**Settings:**
- Generic Author Name: `Acme Clinical Research`
- Form Bookmark Label: `CRF_Pages`
- SDTM Bookmark Label: `Data_Domains`

**Result:**
- All annotations show "Acme Clinical Research" as author
- Bookmarks organized under "CRF_Pages" and "Data_Domains"

### Example 3: Multilingual Configuration
**Settings:**
- Generic Author Name: `Équipe de données`
- Form Bookmark Label: `Formulaires`
- SDTM Bookmark Label: `Domaines_SDTM`

**Result:**
- All annotations show "Équipe de données" as author
- Bookmarks in French: "Formulaires" and "Domaines_SDTM"

## Default Behavior

**Author Name:**
- If left empty → Uses "Geron"
- Placeholder shows "Geron"

**Bookmark Labels:**
- Form label empty → Uses "Form_bookmarks"
- SDTM label empty → Uses "SDTM"
- Placeholders show defaults

## Tips

✅ **DO:**
- Use descriptive names for author and bookmarks
- Save your configuration after making changes
- Use consistent naming across your organization
- Test with a sample PDF first
- Use clear, concise bookmark labels

❌ **DON'T:**
- Leave fields blank if you want custom values (they use defaults)
- Forget to save your configuration
- Use very long labels (keep under 50 characters)
- Use duplicate labels for both bookmark sections

## Troubleshooting

### "My settings aren't being applied"
**Solution:** Make sure you saved the configuration after entering values.

### "Fields show default text but I entered something else"
**Solution:** 
- That's just placeholder text showing defaults
- Look at what you actually typed
- Save and reload to verify settings were saved

### "Bookmarks show default labels"
**Solution:**
- Check that labels were saved in config
- Restart application if it was open when you saved
- Verify in confirmation dialog before standardizing

### "Where are these settings stored?"
**Answer:** In your `config/config.yaml` file under the `validation` section:
```yaml
validation:
  generic_author_name: "Your Name"
  form_bookmark_label: "Your Form Label"
  sdtm_bookmark_label: "Your SDTM Label"
```

## Need More Help?

See detailed documentation:
- `docs/GENERIC_AUTHOR_FEATURE.md` - Author name feature details
- `docs/BOOKMARK_LABELS_FEATURE.md` - Bookmark labels feature details
- `docs/USER_GUIDE.md` - Complete user guide
- `docs/FEATURE_CHANGELOG.md` - What changed and when

---

**Quick Reference:**

| Setting | Default | Location |
|---------|---------|----------|
| Generic Author Name | Geron | Configuration → Validation Settings |
| Form Bookmark Label | Form_bookmarks | Configuration → Validation Settings |
| SDTM Bookmark Label | SDTM | Configuration → Validation Settings |

**When Applied:** During "Standardize Annotations" operation  
**Persistence:** Saved in config.yaml file  
**Confirmation:** All values shown in confirmation dialog before applying


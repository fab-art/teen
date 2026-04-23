# Duka ERP (Streamlit)

Role-based shop management app built with Streamlit + Supabase.

## Local run

```bash
pip install -r requirements.txt
streamlit run Home.py
```

## Streamlit Cloud deployment (optimized)

1. Push this repository to GitHub.
2. In Streamlit Community Cloud, create a new app and set:
   - **Main file path**: `Home.py`
   - **Python dependencies**: `requirements.txt`
3. Add required secrets in the app settings:

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_ANON_OR_SERVICE_KEY"
```

4. Optional user overrides:

```toml
[users.admin]
password = "change_me"
full_name = "Shop Owner"
```

### Included cloud optimizations

- `st.cache_resource` for Supabase client reuse.
- `st.cache_data` dashboard snapshot cache (`ttl=90`) to reduce query volume.
- `.streamlit/config.toml` with `fastReruns = true` and `runOnSave = false` for stable cloud performance.
- Removed committed bytecode/cache artifacts from the repository.

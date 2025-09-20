# Small place to store prompt templates. For demo purposes; use DB in prod.
TEMPLATES = {
    "default": "You are an assistant. Use context and answer: {query}" 
}

def render_template(name, **kwargs):
    tpl = TEMPLATES.get(name, TEMPLATES['default'])
    return tpl.format(**kwargs)

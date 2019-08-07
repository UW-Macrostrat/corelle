from pg_viewtils import relative_path
from sqlalchemy import text

def get_sql(key):
    fn = relative_path(__file__, key+'.sql')
    return text(open(fn).read())

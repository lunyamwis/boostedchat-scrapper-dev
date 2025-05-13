
from jinja2 import Environment, FileSystemLoader
import os


def generate_query(code):
    file_dir  = os.path.dirname(os.path.abspath(f"{__file__}/"))
    print(file_dir)
    env = Environment(loader=FileSystemLoader(file_dir))
    template = env.get_template(f'templates/analyst/query.jinja2')

    
    with open(f"{file_dir}/queries/query.py","w") as f:
        
        f.write(template.render(code=code))



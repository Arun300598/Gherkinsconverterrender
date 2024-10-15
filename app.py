from flask import Flask, render_template, request, send_file
import os
import re

app = Flask(__name__)

# Define the route to serve the sitemap.xml
@app.route('/sitemap.xml')
def sitemap():
    return send_file(os.path.join(app.static_folder, 'sitemap.xml'))

def generate_step_definitions(gherkin_text):
    if not gherkin_text.strip():
        return "Error: Please enter Gherkin text."

    lines = gherkin_text.strip().split('\n')
    step_definitions = {}
    output = []

    # Regex to match <param>, "param", and param (including email)
    param_pattern = re.compile(r'(<[^>]+>|"[^"]+"|[^\s<>]+@[^\s<>]+|[^\s<>]+)')

    for line in lines:
        line = line.strip()

        if line.startswith(('Scenario:', 'Scenario Outline:')):
            continue

        if line.startswith(('Given', 'When', 'Then', 'But', 'And')):
            keyword = line.split()[0]  # Get the keyword
            description = line[len(keyword):].strip()  # Get the description

            # Check if the description includes a DataTable
            if "I have the following user details" in description:
                # Handle DataTable
                step_definition = f"@{keyword}(\"{description}\")\n"
                step_definition += f"public void {re.sub(r'[^a-zA-Z0-9]', '_', description.replace(' ', '_'))}(io.cucumber.datatable.DataTable dataTable) {{\n" \
                                  f"    // Step implementation here\n" \
                                  f"}}\n"
                output.append(step_definition)
                continue  # Skip further processing for this step

            # Replace parameters with {string} using the param_pattern
            description_with_params = param_pattern.sub('{string}', description)

            # Create a method name from the description
            method_name = re.sub(r'[^a-zA-Z0-9]', '_', description.replace(' ', '_'))
            method_name = re.sub(r'_+', '_', method_name).strip('_')  # Remove extra underscores

            # Extract parameter names from description
            param_names = re.findall(param_pattern, description)
            param_declarations = ', '.join(['String string' + str(i + 1) for i in range(len(param_names))])  # Use generic string names

            # Check if the step definition already exists
            step_key = (keyword, description_with_params)
            if step_key not in step_definitions:
                # Format the step definition correctly
                step_definition = f"@{keyword}(\"{description_with_params}\")\n"
                if param_names:
                    step_definition += f"public void {method_name}({param_declarations}) {{\n" \
                                       f"    // Step implementation here\n" \
                                       f"}}\n"
                else:
                    step_definition += f"public void {method_name}() {{\n" \
                                       f"    // Step implementation here\n" \
                                       f"}}\n"
                
                output.append(step_definition)
                step_definitions[step_key] = method_name  # Mark this step as defined

    return ''.join(output)

@app.route('/', methods=['GET', 'POST'])
def index():
    output = ''
    gherkin_text = ''
    if request.method == 'POST':
        gherkin_text = request.form['gherkin_text']
        output = generate_step_definitions(gherkin_text)

    return render_template('index.html', gherkin_text=gherkin_text, output=output)

if __name__ == '__main__':
    app.run(debug=True)

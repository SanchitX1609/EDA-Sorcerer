import pandas as pd
from ydata_profiling import ProfileReport
from bs4 import BeautifulSoup
import requests
import base64
import os
import shutil
import cairosvg
from openai import OpenAI
from autogen import ConversableAgent
from autogen import register_function

Dataset_path = 'bank_transactions.csv' #paste your dataset path here
API_KEY = 'Paste your OpenAI key here!!' #paste your OpenAI key here
model = 'gpt-4o' #paste your gpt engine here
df1 = pd.read_csv(Dataset_path)

profile = ProfileReport(df1, title="Profiling Report", explorative=True)
profile.to_file("profiling_report.html")

# Read the HTML content from the file
with open("profiling_report.html", "r", encoding="utf-8") as file:
    html_content = file.read()

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(html_content, "html.parser")
svg_elements = soup.find_all('svg')

# Directories for saving SVG and PNG files
svg_output_dir = 'svg_outputs'
png_output_dir = 'png_outputs'
os.makedirs(svg_output_dir, exist_ok=True)
os.makedirs(png_output_dir, exist_ok=True)

# Function to convert units to pixels
def convert_to_pixels(value):
    if value.endswith('pt'):
        return int(float(value[:-2]) * 1.333)  # 1pt = 1.333px
    elif value.endswith('cm'):
        return int(float(value[:-2]) * 37.795)  # 1cm = 37.795px
    elif value.endswith('mm'):
        return int(float(value[:-2]) * 3.7795)  # 1mm = 3.7795px
    elif value.endswith('in'):
        return int(float(value[:-2]) * 96)  # 1in = 96px
    elif value.endswith('px'):
        return int(value[:-2])
    else:
        return int(value)

# Counter for SVG elements
svg_counter = 0

# Maximum allowable size for width and height in pixels
MAX_SIZE = 10000

for svg in svg_elements:
    # Get or set default width and height
    width = svg.get('width', '1000')  # Default to 1000 if width is not specified
    height = svg.get('height', '500')  # Default to 500 if height is not specified

    # Convert width and height to pixels
    width_in_pixels = convert_to_pixels(width)
    height_in_pixels = convert_to_pixels(height)

    # Ensure dimensions do not exceed maximum allowable size
    if width_in_pixels > MAX_SIZE:
        width_in_pixels = MAX_SIZE
    if height_in_pixels > MAX_SIZE:
        height_in_pixels = MAX_SIZE

    # Update SVG dimensions
    svg['width'] = f"{width_in_pixels}px"
    svg['height'] = f"{height_in_pixels}px"

    svg_filename = f"svg_{svg_counter}.svg"
    png_filename = f"svg_{svg_counter}.png"

    # Convert the BeautifulSoup SVG object to a string
    svg_content = str(svg)

    # Save the SVG content to a file
    svg_filepath = os.path.join(svg_output_dir, svg_filename)
    with open(svg_filepath, "w", encoding="utf-8") as svg_file:
        svg_file.write(svg_content)

    # Convert the SVG file to a PNG file
    png_filepath = os.path.join(png_output_dir, png_filename)
    try:
        cairosvg.svg2png(url=svg_filepath, write_to=png_filepath)
        print(f"SVG {svg_counter} saved as {svg_filename} and converted to {png_filename}")
    except Exception as e:
        print(f"Error converting SVG {svg_counter}: {e}")

    svg_counter += 1

print(f"Found and saved {svg_counter} SVG elements.")

profile.get_description().correlations['auto'].to_csv('correlations.csv')

pd.DataFrame(profile.get_description().variables).T.to_csv('description.csv')

png_output_dir = 'png_outputs'


files = os.listdir(png_output_dir)
png_files = [file for file in files if file.endswith('.png')]

system_message = {
    "role": "system",
    "content": "You are an Image Analyst. Your only job is to explain the insights you found. If you weave a story, don't make it complicated and don't go about creating new characters."
}

def encode_image(image_path):
    with open(image_path,"rb") as image:
        return base64.b64encode(image.read()).decode('utf-8')

os.makedirs('png_desc', exist_ok=True)

for png_file in png_files:
  image_path = os.path.join(png_output_dir, png_file)
  base64_image = encode_image(image_path)

  user_message = {
          "role": "user",
          "content": [
              {"type": "text", "text": """
      Task: Analyze the Charts and Visualizations

      Objective: Examine the charts and visualizations in the provided image and extract useful insights.

      Instructions:
      1. Identify the Types of Charts and Visualizations:
        - Describe each chart and visualization type (e.g., bar chart, line graph, pie chart, scatter plot, etc.).

      2. Summarize Key Data Points:
        - Highlight significant data points, trends, and patterns visible in each chart.
        - Note any anomalies or outliers.

      3. Interpret Trends and Patterns:
        - Provide an analysis of the trends and patterns observed.
        - Explain the potential implications or insights that can be derived from these trends.

      4. Compare and Contrast Data:
        - If there are multiple charts, compare and contrast the data they present.
        - Identify any correlations or discrepancies between the different visualizations.

      5. Conclusions and Recommendations:
        - Summarize the overall findings from the analysis.
        - Offer any recommendations or actions that might be taken based on the insights derived from the data.

      Output Format:
      Provide the analysis in JSON format as follows:

      {
        "charts": [
          {
            "plot_type": "Type of the chart (e.g., bar chart, line graph, etc.)",
            "plot_about": "Brief description of what the chart is about",
            "description": "Detailed description inferred from the data",
            "information": "Key information and insights derived from the data"
        """ },

              {
                  "type": "image_url",
                  "image_url": {
                      "url": f"data:image/png;base64,{base64_image}",
                  },
              }
          ]
  }

  client = OpenAI(api_key = API_KEY)
  response = client.chat.completions.create(
      model=model,
      messages=[system_message, user_message],
      max_tokens=300,
  )

  png_filename = png_file[:-4]+'.txt'
  os.makedirs('png_desc', exist_ok=True)
  png_filepath = os.path.join('png_desc', png_filename)
  with open(png_filepath, "w", encoding="utf-8") as nfile:
      nfile.write(response.choices[0].message.content)


os.makedirs('Work_dir', exist_ok=True)
shutil.move('correlations.csv', 'Work_dir/correlations.csv')
shutil.move('description.csv', 'Work_dir/description.csv')
shutil.move('png_desc', 'Work_dir/png_desc')
shutil.move('png_outputs', 'Work_dir/png_outputs')

def get_files_from_dir(directory: str = 'Work_dir'):
    descriptions = {}
    charts = {}
    csv_files = {}

    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            if filename.endswith('.txt'):  # Assuming descriptions are in .txt files
                with open(file_path, 'r') as file:
                    descriptions[filename] = file.read()
            elif filename.endswith('.png'):  # Assuming charts are in image format
                charts[filename] = file_path  # Store the path to the image file
            elif filename.endswith('.csv'):  # Assuming CSV files for data
                with open(file_path, 'r') as file:
                    csv_files[filename] = file.read()  # Store the CSV content as a string

    return charts, descriptions, csv_files

charts, descriptions, csv_files = get_files_from_dir()

stringg = f"{charts,descriptions,csv_files}"

analysis_agent = ConversableAgent(
    name="Analysis_Agent",
    system_message="""

You are to look into the set dictionaries I gave above.
Your task is to analyze a comprehensive set of input data, consisting of various charts located in one folder and corresponding descriptions in another folder. The filenames for the charts and their respective descriptions are the same, ensuring easy correlation between them.

Begin by thoroughly reviewing the descritptions of the charts and their summaries to identify key patterns, significant correlations, and notable anomalies. Utilize advanced data visualization techniques to effectively communicate these key insights and trends. Focus on highlighting findings that underscore their relevance and potential impact.

Data Review:

Examine each chart to understand the visual representation of the data.
Refer to the corresponding description files to get detailed explanations of each chart.
Identify Key Insights:

Look for significant patterns, trends, and anomalies in the charts.
Formulate hypotheses based on the observed patterns and correlations.

Statistical Validation:

Validate the hypotheses using appropriate statistical methods.
Where possible, compare the identified trends to industry benchmarks or best practices to provide context and highlight areas for potential improvement.
Visual Communication:

Use advanced data visualization techniques to effectively communicate the key insights and trends. When utilizing an image would be useful in the set of dictionaries i gave you, include the path of the image that would be useful and embed the path to where you think it would be useful in your response.
Ensure the analysis is visually appealing and clearly articulated to facilitate quick understanding and decision-making by stakeholders.
Actionable Insights:

Highlight clear and actionable insights that are easily understandable to users.
Suggest areas for further investigation, explaining why these areas may warrant deeper exploration.
Concise Overview:

Distill the essence of the data into a brief but informative overview. Also when you are giving actionable insights, use the actual figures (numbers) in the description to support your claim and include those real figures in your response.
When Iamges would be useful, include the path of the image that would be useful and embed the path to where you think it would be useful in your response. The image in question must be in the list I gave you.
Enable stakeholders to grasp the critical insights quickly and make informed decisions.
Goal:

The goal is to provide a high-level overview that captures the most significant trends and insights from the charts, ensuring the analysis is concise yet comprehensive, visually appealing, and clearly articulated. This will enable stakeholders to understand the critical insights quickly and make informed decisions.
""",

    llm_config={"config_list": [{"model": model, "api_key": API_KEY}]},
)

critique = ConversableAgent(
    name="Critique_Agent",
    system_message="""

Make sure that the acutal figures in the data are used to support the agents claim. The points should be supported by sufficient amount of figures associated to them. Include the relevant figures whereever you can to make it more understandable.
Your task is to critically evaluate the analysis provided by the first agent, focusing on the clarity, accuracy, and effectiveness of the insights presented. Your critique should cover the following aspects:

Clarity and Comprehensibility:

Assess whether the analysis is easy to understand for stakeholders.
Identify any areas where the language or visualizations are confusing or ambiguous.
Suggest improvements to enhance clarity and readability.
Accuracy and Validity:

Verify the accuracy of the key insights and trends identified by the first agent.
Ensure that the statistical methods used to validate hypotheses are appropriate and correctly applied.
Check for any inconsistencies or errors in the data interpretation.
Relevance and Impact:

Evaluate whether the findings highlighted by the first agent are relevant and impactful.
Determine if the insights are aligned with industry benchmarks or best practices.
Suggest additional context or comparisons that could enhance the analysis.
Visual Communication:

Review the effectiveness of the data visualization techniques used.
Identify any charts or visualizations that could be improved for better communication of insights.
Recommend alternative visualization techniques if necessary.
Actionable Insights:

Assess whether the insights provided are actionable and practical for stakeholders.
Suggest any additional areas for investigation that may have been overlooked.
Ensure that the suggestions for further exploration are well-justified and relevant.
Overall Quality:

Provide an overall assessment of the analysis, highlighting strengths and areas for improvement.
Offer constructive feedback to help refine and enhance the analysis.
Goal:

The goal is to fine-tune the analysis by ensuring it is clear, accurate, relevant, and effectively communicated. Your critique should provide constructive feedback that enhances the overall quality of the insights, making them more actionable and impactful for stakeholders.

""",

    llm_config={"config_list": [{"model": model, "api_key": API_KEY}]},
)

chat_result = critique.initiate_chat(
    analysis_agent,
    message=f"You need to work on these {stringg}" +"""You are to start your introduction as follows !The analysis presented here delves into various facets of customer transactions, demographic distributions, and data integrity within the organization. Through visualizations and comprehensive descriptions, this narrative aims to demystify the dataset, revealing critical trends, correlations, and anomalies that can drive meaningful change! You are to look into the set dictionaries I gave above. Distill the essence of the data into a brief but informative overview. Also when you are giving actionable insights, use the actual figures (numbers) in the description to support your claim and include those real figures in your response.
When Iamges would be useful, include the path of the image that would be useful and embed the path to where you think it would be useful in your response. The image in question must be in the list I gave you.
Enable stakeholders to grasp the critical insights quickly and make informed decisions. Don't anaylse the visualizations, I have already done so and included their desciption with the same name in another folder named png_desc. Refer to that. Keep in mind the useful insights you found in the information provided to take further action.The goal is to provide a high-level overview that captures the most significant trends and insights from the charts, ensuring the analysis is concise yet comprehensive, visually appealing, and clearly articulated. This will enable stakeholders to understand the critical insights quickly and make informed decisions in a story kind of way.
    Craft a compelling narrative that transforms the data insights into a story that resonates with the audience and drives meaningful change within the organization. Begin with an introduction that sets the context and purpose of the analysis, clearly explaining why this data is important and how it will be used. Use the visualizations produced by the Code Executor Agent to support and enhance your story, ensuring they are seamlessly integrated to illustrate key points effectively.
Guide the audience through the narrative by highlighting the most significant findings, trends, and anomalies. Explain their relevance and implications in a clear, engaging manner, ensuring your explanations connect the insights to the broader business context. As you uncover these insights, avoid technical jargon and tailor your language to be easily understandable for the intended audience.
Structure the narrative logically and coherently. Start by setting the stage to provide background information, then move on to highlight key findings, uncover anomalies, and connect the dots between different insights. Propose actionable recommendations based on the data, explaining how they can address identified issues or leverage opportunities. Discuss potential risks and how they might be mitigated.
Conclude with a compelling summary that reinforces the value of the insights and inspires action. Ensure your narrative captivates the audience, demonstrates the importance of the findings, and provides a clear path forward. Your goal is to create a story that not only presents the data but also motivates stakeholders to act on the insights, leading to informed decision-making and positive organizational change.
""",
    summary_method="reflection_with_llm",
    max_turns = 2
)

chat_result.chat_history[-1]['content']

output = chat_result.chat_history[-1]['content']

system_message = {'role':'system','content':'''You convert the input I give you to an html file and Whereever theres a image path in the input, you job is to display the image in the html file using the path. Create an HTML page with a modern and aesthetic design. Use the following guidelines:

Make the aesthetic and visually appealing. Put the image at the center not left or right. and make sure the border is like just 10 percent bigger than the size of the image so it surrounds the image and make it look like the image is floating inside and make sure the border is not too thick.
Mkae the image zoom in when you hover over them.
Layout:

Use a clean and responsive layout with a header, main content section, and footer.
Center the content and make it visually appealing with appropriate spacing and alignment.
Typography:

Use modern and stylish fonts from Google Fonts.
Ensure good readability with proper font sizes, line heights, and contrast.
Colors:

Choose a modern and harmonious color palette.
Use a combination of soft and vibrant colors for different elements like background, text, and buttons.
Imagery:

Include high-quality images that complement the design.
Use images with appropriate size and resolution for faster loading.
Navigation:

Implement a sleek and intuitive navigation bar with hover effects.
Ensure the navigation bar is sticky at the top.
Buttons and Links:

Style buttons and links with modern effects like shadows, gradients, and transitions.
Use hover and active states for interactive elements.
Forms:

Design clean and user-friendly forms with proper input fields and labels.
Include modern elements like floating labels or minimalistic styles.
Animations:

Incorporate subtle animations and transitions to enhance the user experience.
Ensure animations are smooth and do not hinder performance.
Footer:

Design a minimalistic footer with links to social media and other important information.
For instagram :- https://www.instagram.com/sanchit_1609/?hl=en
linkedin :- https://www.linkedin.com/in/sanchit-jain-4492b11b6/
Ensure the footer is visually consistent with the rest of the page.
Overall Aesthetic:

Maintain a balance between aesthetics and functionality.
Use modern design principles to create a visually appealing and user-friendly interface.
'''}
user_message = {'role':'user','content':f'{output}'+"Convert the above input to an html file and Whereever theres a image path in the input, you job is to display the image in the html file using the path. Add CSS and Javascipt too to make the html page interactive and stylish."}

client = OpenAI(api_key = API_KEY)
response = client.chat.completions.create(
      model=model,
      messages=[system_message, user_message],
      max_tokens=4096,
  )

file_path = "report.html"

# Save the content to a file with .html extension
with open(file_path, "w") as file:
    file.write(response.choices[0].message.content)


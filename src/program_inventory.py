import os
import pandas as pd
from typing import Dict, List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

load_dotenv()

class ProgramInventoryAgent:
    def __init__(self):
        # Initialize OpenAI client with API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
            
        self.llm = ChatOpenAI(
            api_key=api_key,
            model="gpt-4",
            temperature=0.5
        )
        
        # Program inference prompt template
        self.program_inference_prompt = ChatPromptTemplate.from_template("""
        Based on the following department personnel data and website:

        Personnel Data:
        {personnel_data}

        Website: {website_url}

        Please predict exactly {programs_per_department} programs that are likely provided as well as program descriptions. 
        DO NOT GENERATE FEWER THAN {programs_per_department} PROGRAMS.

        For each program, numbered 1 through {programs_per_department}, use exactly this format:

        1. Program Name: [name]
        Description: [description]
        Key Positions: [positions]
        Website Alignment: [alignment]

        (Continue numbering through {programs_per_department})

        Make sure to include all {programs_per_department} programs with the numbered prefix and exact section headers as shown above.
        """)

    def read_excel_data(self, file_path: str) -> pd.DataFrame:
        """Read the input Excel file"""
        try:
            df = pd.read_excel(file_path)
            # Clean column names by stripping whitespace
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            raise

    def format_personnel_data(self, df: pd.DataFrame, department: str) -> str:
        """Format personnel data for a specific department"""
        dept_data = df[df['Department'] == department]
        divisions = dept_data['Division'].unique()
        formatted_data = f"Department: {department}\n"
        
        for division in divisions:
            div_positions = dept_data[dept_data['Division'] == division]['Position Name'].unique()
            formatted_data += f"\nDivision: {division}\n"
            formatted_data += f"Positions: {', '.join(div_positions)}\n"
        
        return formatted_data

    def parse_llm_response(self, response: str) -> List[Dict]:
        """Parse the LLM response into structured program data"""
        programs = []
        current_program = {}
        
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith(tuple(f"{i}." for i in range(1, 51))):  # Handle up to 50 programs
                if current_program:
                    programs.append(current_program)
                current_program = {}
                program_name_part = line.split(':', 1)
                if len(program_name_part) > 1:
                    current_program['Program Name'] = program_name_part[1].strip()
            elif line.startswith('Description:'):
                current_program['Description'] = line.split(':', 1)[1].strip()
            elif line.startswith('Key Positions:'):
                current_program['Key Positions'] = line.split(':', 1)[1].strip()
            elif line.startswith('Website Alignment:'):
                current_program['Website Alignment'] = line.split(':', 1)[1].strip()
        
        if current_program:
            programs.append(current_program)
            
        return programs

    def generate_programs(self, personnel_data: str, website_url: str, programs_count: int) -> List[Dict]:
        """Generate program descriptions using LLM"""
        print(f"Requesting {programs_count} programs...")
        
        chain = LLMChain(
            llm=self.llm,
            prompt=self.program_inference_prompt
        )
        
        result = chain.invoke({
            "personnel_data": personnel_data,
            "website_url": website_url,
            "programs_per_department": programs_count
        })
        
        # Parse the response into structured format
        programs = self.parse_llm_response(result['text'])
        print(f"Received {len(programs)} programs from LLM")
        
        if len(programs) < programs_count:
            print(f"Warning: Only received {len(programs)} programs when {programs_count} were requested")
        
        return programs

    def process_department(self, df: pd.DataFrame, department: str, website_url: str, programs_count: int) -> pd.DataFrame:
        """Process a single department and return programs DataFrame"""
        personnel_data = self.format_personnel_data(df, department)
        programs = self.generate_programs(personnel_data, website_url, programs_count)
        
        # Convert to DataFrame
        programs_df = pd.DataFrame(programs)
        programs_df['Department'] = department
        
        # Reorder columns to match desired output
        column_order = ['Department', 'Program Name', 'Description', 'Key Positions', 'Website Alignment']
        programs_df = programs_df[column_order]
        
        return programs_df
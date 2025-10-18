### **Instructions for Participants: AIAC 2025 Code Submission**  

Welcome to the **AI Alphas Competition (AIAC) 2025**! Below are detailed instructions to help you use the provided template  to interact with the WorldQuant Brain API and a Large Language Model (LLM) to process alpha expressions.  

---

#### **Code Template**  
The provided Python template includes three main functions:  

1. **`call_llm(prompt)`**  
   - Interface with your preferred LLM to process prompts.  
   - Replace the example OpenAI GPT implementation with your own LLM logic.  

2. **`generate_alpha_description(alpha_id, brain_session)`**  
   - Generates a plain English description of an Alpha using the BRAIN API and LLM.  

3. **`generate_new_alphas(alpha_description, brain_session)`**  
   - Creates new Alpha expressions based on the generated description using information from BRAIN API (eg operators and data fields).  

---

#### **Steps to Follow**  

##### **Step 1: Setup**  
1. Install the required Python libraries:  
   ```bash
   pip install pandas nest_asyncio openai
   ```  
2. Replace `"your-api-key"` in the `call_llm` function with your LLM API key.

---

##### **Step 2: Generate Alpha Descriptions**  
1. List your Alpha IDs in the `alpha_ids` variable.  
2. Use the `generate_alpha_description` function to generate plain English descriptions for each Alpha.  
3. The function will:  
   - Retrieve Alpha details from the BRAIN API.  
   - Use operators and data fields to create a prompt for the LLM.  
   - Return a detailed description of the alpha.  
4. Edit this function to refine generated descriptions.

---

##### **Step 3: Generate New Alphas**  
1. Use the `generate_new_alphas` function to create new Alpha expressions based on the descriptions.  
2. The function will:  
   - Use operators and data fields to create a prompt for the LLM.  
   - Generate new Alpha expressions following the rules for **PowerPool** and **ATOM** Alphas.  
3. Edit this function to ensure the generated Alphas are unique and can be run on the platform.  

---

##### **Step 4: Simulate, Tag and add Descirption to Alphas**  
1. Use the ACE Library to simulate the generated Alphas.  
2. Tag each child Alpha with its parent Alpha ID.
3. Add description to child Alphas.  
4. Example logic for simulation and tagging:  
   ```python
   simulate_data = ace.generate_alpha(brain_session, regular=...)
   simulation_result = ace.simulate_single_alpha(brain_session, simulate_data)
   child_alpha_id = simulation_result['alpha_id']
   ace.set_alpha_properties(brain_session, child_alpha_id, tags=[f"parent_alpha_id"], , regular_desc = generate_alpha_description(child_alpha_id, brain_session))
   ```  
5. Edit this function to implement your own logic.

---

#### **Submission Requirements**  
1. **SuperAlphas** must be built using child Alphas linked to the same parent Alpha ID.  
2. Submit your **SuperAlphas** and machine (code) via the platform form.  
3. Only your **last machine submission** will be considered.  

---

#### **Important Notes**  
- **Minimum Submissions:** You must submit at least **10 Super Alphas** to be eligible for stipends.  
- **Component Alphas:** Only **PowerPool** or **ATOM** Alphas are allowed as components.  
- **PowerPool Descriptions:** Input LLM Alpha description to the Idea section of PowerPool Alpha description.
- **Tagging:** Ensure all child Alphas are tagged with their parent Alpha ID and have a description.  
- **LLM Usage:** You may use any LLM of your choice, but ensure compliance with the provided template.  

---

#### **Key Dates**  
- **October 13, 2025:** Submissions start  
- **November 23, 2025:** Submissions end  

---

#### **Support**  
For any questions or technical issues, refer to the **ACE Library Documentation**, **FAQs**, **Competition Guidelines** or contact the **WorldQuant BRAIN Team**.  

Good luck, and we look forward to seeing your innovative submissions!  
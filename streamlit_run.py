import streamlit as st
import requests
import json
from PIL import Image
import io
import os
import tempfile
import time
from typing import Optional

# Configure Streamlit page
st.set_page_config(
    page_title="AI Skincare Recommendation System",
    page_icon="🧴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Background image for main app */
    .stApp {
        background-image: url('https://i.postimg.cc/hXztbbsn/image.png');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    
    /* Background overlay for better readability */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.85);
        z-index: -1;
    }
    
    /* Sidebar background */
    .css-1d391kg {
        background-image: url('https://i.postimg.cc/hXztbbsn/image.png');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }
    
    /* Sidebar overlay */
    .css-1d391kg::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.9);
        z-index: 0;
    }
    
    /* Ensure sidebar content is above overlay */
    .sidebar .sidebar-content {
        position: relative;
        z-index: 1;
    }
    
    .main-header {
        text-align: center;
        color: #FF6B6B;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .sub-header {
        text-align: center;
        color: #4ECDC4;
        font-size: 1.2rem;
        margin-bottom: 3rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    .recommendation-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 20px 0;
        backdrop-filter: blur(5px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .analysis-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 20px 0;
        backdrop-filter: blur(5px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .success-box {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 20px 0;
        backdrop-filter: blur(5px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: bold;
        width: 100%;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    /* Content boxes with better visibility */
    .block-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        margin: 10px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'uploaded_file_data' not in st.session_state:
    st.session_state.uploaded_file_data = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None
if 'selected_goal' not in st.session_state:
    st.session_state.selected_goal = ''

# Backend Logic - Moved from FastAPI to Streamlit
@st.cache_data
def calculate_brightness(image_bytes):
    """Calculate average brightness of the uploaded image"""
    try:
        # Open image from bytes
        img = Image.open(io.BytesIO(image_bytes)).convert('L')  # Convert to grayscale
        
        # Calculate average brightness
        brightness = sum(img.getdata()) / (img.width * img.height)
        return round(brightness, 2)
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None

def get_skincare_recommendation(goal: str, history: str, brightness: float):
    """Get skincare recommendation using Hugging Face API or local fallback"""
    
    # Construct prompt for skincare recommendation
    prompt = f"""
    As a skincare expert, provide a recommendation based on:
    - Skincare Goal: {goal}
    - Past Product History: {history}
    - Skin Brightness Score: {brightness}/255 (higher means brighter skin)
    
    Please provide:
    1. A specific skincare routine recommendation
    2. Key ingredients to look for
    3. Products to avoid
    4. Expected timeline for results
    
    Keep the response concise and professional.
    """
    
    # Fallback local recommendation function
    def get_local_recommendation():
        recommendations = {
            "brightening": {
                "routine": "Use Vitamin C serum in morning, Niacinamide serum at night, and always apply SPF 30+",
                "key_ingredients": "Vitamin C, Niacinamide, Alpha Arbutin, Kojic Acid",
                "avoid": "Harsh scrubs, over-exfoliation, products with alcohol",
                "timeline": "4-8 weeks for visible results"
            },
            "anti-aging": {
                "routine": "Retinol at night, Hyaluronic acid serum, and broad-spectrum sunscreen daily",
                "key_ingredients": "Retinol, Peptides, Hyaluronic Acid, Vitamin E",
                "avoid": "Mixing retinol with AHA/BHA, sun exposure without SPF",
                "timeline": "6-12 weeks for visible results"
            },
            "acne": {
                "routine": "Salicylic acid cleanser, Benzoyl peroxide spot treatment, oil-free moisturizer",
                "key_ingredients": "Salicylic Acid, Benzoyl Peroxide, Niacinamide, Tea Tree Oil",
                "avoid": "Over-cleansing, heavy oils, comedogenic ingredients",
                "timeline": "2-6 weeks for improvement"
            },
            "hydration": {
                "routine": "Gentle cleanser, Hyaluronic acid serum, rich moisturizer, and gentle SPF",
                "key_ingredients": "Hyaluronic Acid, Ceramides, Glycerin, Squalane",
                "avoid": "Alcohol-based products, harsh exfoliants, over-cleansing",
                "timeline": "2-4 weeks for improved hydration"
            },
            "oil control": {
                "routine": "Foaming cleanser, BHA toner, oil-free moisturizer, mattifying SPF",
                "key_ingredients": "Salicylic Acid, Niacinamide, Clay, Zinc Oxide",
                "avoid": "Over-cleansing, heavy oils, alcohol-based astringents",
                "timeline": "3-6 weeks for oil balance"
            },
            "sensitive": {
                "routine": "Gentle cream cleanser, fragrance-free moisturizer, mineral SPF",
                "key_ingredients": "Ceramides, Colloidal Oatmeal, Allantoin, Zinc Oxide",
                "avoid": "Fragrances, essential oils, harsh actives, over-exfoliation",
                "timeline": "2-4 weeks for reduced sensitivity"
            }
        }
        
        # Match goal to recommendation
        goal_lower = goal.lower()
        for key in recommendations.keys():
            if key in goal_lower:
                return recommendations[key]
        
        # Check for specific keywords
        if any(word in goal_lower for word in ["bright", "glow", "even", "dark"]):
            return recommendations["brightening"]
        elif any(word in goal_lower for word in ["aging", "wrinkle", "fine", "line"]):
            return recommendations["anti-aging"]
        elif any(word in goal_lower for word in ["acne", "pimple", "breakout", "blemish"]):
            return recommendations["acne"]
        elif any(word in goal_lower for word in ["dry", "hydrat", "moisture"]):
            return recommendations["hydration"]
        elif any(word in goal_lower for word in ["oily", "oil", "shine", "mattify"]):
            return recommendations["oil control"]
        elif any(word in goal_lower for word in ["sensitive", "irritat", "red"]):
            return recommendations["sensitive"]
        
        # Default recommendation
        return {
            "routine": "Gentle cleanser, moisturizer suited for your skin type, and daily SPF protection",
            "key_ingredients": "Hyaluronic Acid, Ceramides, Niacinamide",
            "avoid": "Harsh ingredients, over-exfoliation",
            "timeline": "4-6 weeks for visible results"
        }
    
    # Try Hugging Face API first (if API key is available)
    hf_api_key = "hf_bYQPJEhXsXRODCujrBNQYOxOzLsNSJvWV"
    
    if hf_api_key:
        try:
            headers = {"Authorization": f"Bearer {hf_api_key}"}
            api_url = "https://api-inference.huggingface.co/models/gpt2"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_length": 200,
                    "temperature": 0.7,
                    "do_sample": True
                }
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get('generated_text', '')
                    recommendation_text = generated_text.replace(prompt, '').strip()
                    
                    if recommendation_text:
                        return {
                            "recommendation": recommendation_text,
                            "source": "AI Generated"
                        }
        
        except Exception as e:
            st.warning(f"AI API temporarily unavailable, using expert recommendations instead.")
    
    # Return local recommendation as primary or fallback
    return get_local_recommendation()

def process_skincare_request(image_bytes, goal, history):
    """Process the complete skincare recommendation request"""
    try:
        # Calculate brightness
        brightness_score = calculate_brightness(image_bytes)
        
        if brightness_score is None:
            return None, "Failed to process image"
        
        # Get skincare recommendation
        recommendation = get_skincare_recommendation(goal, history, brightness_score)
        
        # Create response
        response = {
            "analysis": {
                "brightness_score": brightness_score,
                "brightness_level": "High" if brightness_score > 200 else "Medium" if brightness_score > 100 else "Low",
                "image_processed": True
            },
            "recommendation": recommendation,
            "user_input": {
                "goal": goal,
                "history": history
            },
            "mock_collection_link": f"https://skincare-collection.com/recommended/{goal.lower().replace(' ', '-')}",
            "status": "success"
        }
        
        return response, None
        
    except Exception as e:
        return None, f"Processing error: {str(e)}"

def display_results(result):
    """Display the API results in a nice format"""
    
    # Analysis Results
    st.markdown('<div class="analysis-box">', unsafe_allow_html=True)
    st.markdown("### 📊 Image Analysis Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Brightness Score",
            value=f"{result['analysis']['brightness_score']}/255",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Brightness Level",
            value=result['analysis']['brightness_level'],
            delta=None
        )
    
    with col3:
        st.metric(
            label="Processing Status",
            value="✅ Success" if result['analysis']['image_processed'] else "❌ Failed",
            delta=None
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Recommendations
    st.markdown('<div class="recommendation-box">', unsafe_allow_html=True)
    st.markdown("### 💡 AI-Powered Skincare Recommendations")
    
    recommendation = result['recommendation']
    
    if isinstance(recommendation, dict):
        # Structured recommendation
        if 'routine' in recommendation:
            st.markdown(f"**🔄 Recommended Routine:**")
            st.write(recommendation['routine'])
        
        if 'key_ingredients' in recommendation:
            st.markdown(f"**🧪 Key Ingredients to Look For:**")
            st.write(recommendation['key_ingredients'])
        
        if 'avoid' in recommendation:
            st.markdown(f"**⚠️ Products/Ingredients to Avoid:**")
            st.write(recommendation['avoid'])
        
        if 'timeline' in recommendation:
            st.markdown(f"**⏰ Expected Timeline:**")
            st.write(recommendation['timeline'])
        
        if 'recommendation' in recommendation:
            st.markdown(f"**📝 AI Generated Advice:**")
            st.write(recommendation['recommendation'])
            if 'source' in recommendation:
                st.caption(f"Source: {recommendation['source']}")
    else:
        # Simple text recommendation
        st.write(recommendation)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Additional Info
    st.markdown('<div class="success-box">', unsafe_allow_html=True)
    st.markdown("### 🔗 Additional Resources")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Your Input Summary:**")
        st.write(f"**Goal:** {result['user_input']['goal']}")
        st.write(f"**History:** {result['user_input']['history']}")
    
    with col2:
        st.markdown("**Recommended Products:**")
        st.markdown("🛒 [**Visit Dermatics India**](https://dermatics.in/) - Get premium skincare products delivered to your doorstep!")
        
        st.markdown("**📱 Save these recommendations for your skincare journey!**")
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🧴 AI Skincare Recommendation System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Get personalized skincare advice powered by AI and advanced image analysis</p>', unsafe_allow_html=True)
    

    
    # Sidebar for instructions
    with st.sidebar:
        st.markdown("### 📋 How to Use")
        st.markdown("""
        1. **Upload Your Photo** - Clear face image works best
        2. **Set Your Goal** - What do you want to achieve?
        3. **Add Your History** - Products you've used before
        4. **Get Recommendations** - AI will analyze and suggest
        """)
        
        st.markdown("### 💡 Tips")
        st.markdown("""
        - Use natural lighting for photos
        - Be specific about your skincare goals
        - Include brand names in product history
        - Consider allergies and skin sensitivity
        """)
        
        st.markdown("### 🎯 Popular Goals")
        goals = [
            "Brightening", "Anti-aging", "Acne treatment", 
            "Hydration", "Oil control", "Sensitive skin care",
            "Pore minimization", "Dark circles", "Rosacea care"
        ]
        for goal in goals:
            if st.button(f"💡 {goal}", key=f"goal_{goal}"):
                st.session_state.selected_goal = goal
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📸 Upload Your Photo")
        uploaded_file = st.file_uploader(
            "Choose a clear face image",
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear photo of your face for skin analysis",
            key="file_uploader"
        )
        
        # Store uploaded file data in session state
        if uploaded_file is not None:
            st.session_state.uploaded_file_data = uploaded_file.getvalue()
            st.session_state.uploaded_file_name = uploaded_file.name
            
            # Display uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_container_width=True)
            
            # Image info
            st.info(f"📏 Image size: {image.size[0]}x{image.size[1]} pixels")
        
        # Show previously uploaded image if exists
        elif st.session_state.uploaded_file_data is not None:
            image = Image.open(io.BytesIO(st.session_state.uploaded_file_data))
            st.image(image, caption=f"Current Image: {st.session_state.uploaded_file_name}", use_container_width=True)
            st.info(f"📏 Image size: {image.size[0]}x{image.size[1]} pixels")
            st.success("✅ Image loaded and ready for analysis!")
    
    with col2:
        st.markdown("### 🎯 Your Skincare Goals")
        
        # Goal dropdown
        skincare_goals = [
            "Select your skincare goal",
            "Brightening and evening skin tone",
            "Anti-aging and wrinkle reduction", 
            "Acne treatment and oil control",
            "Hydration for dry skin",
            "Sensitive skin care routine",
            "Pore minimization",
            "Dark circles and under-eye care",
            "Rosacea and redness reduction",
            "Hyperpigmentation treatment",
            "Blackhead and whitehead removal",
            "Firming and tightening",
            "Sun damage repair",
            "Melasma treatment",
            "Eczema and dermatitis care",
            "Oil control and mattifying",
            "Exfoliation and skin renewal",
            "Barrier repair and protection",
            "Anti-inflammatory treatment",
            "Skin texture improvement",
            "Natural glow enhancement"
        ]
        
        goal_input = st.selectbox(
            "What's your main skincare goal?",
            options=skincare_goals,
            help="Select your primary skincare concern",
            key="goal_selector"
        )
        
        # Previous products dropdown
        previous_products = [
            "Select products you've used",
            "Vitamin C serum",
            "Niacinamide serum",
            "Retinol/Retinoid products",
            "Hyaluronic acid serum",
            "Salicylic acid products",
            "Benzoyl peroxide treatments",
            "AHA/BHA exfoliants",
            "Peptide serums",
            "Ceramide moisturizers",
            "Sunscreen/SPF products",
            "Tea tree oil treatments",
            "Kojic acid products",
            "Alpha arbutin serum",
            "Azelaic acid treatments",
            "Glycolic acid products",
            "Lactic acid treatments",
            "Zinc oxide products",
            "Collagen serums",
            "Bakuchiol products",
            "Squalane oil",
            "Rosehip oil",
            "Argan oil treatments",
            "Centella asiatica products",
            "Snail mucin products",
            "Clay masks",
            "Charcoal treatments",
            "Chemical peels",
            "Microneedling treatments",
            "LED light therapy",
            "None of the above"
        ]
        
        history_input = st.multiselect(
            "Previous skincare products used:",
            options=previous_products,
            help="Select all products you've used before (you can select multiple)",
            key="history_selector"
        )
        
        # Additional options
        st.markdown("### ⚙️ Additional Options")
        
        skin_type = st.selectbox(
            "Skin Type (optional)",
            ["Not specified", "Oily", "Dry", "Combination", "Sensitive", "Normal"],
            key="skin_type_selector"
        )
        
        age_range = st.selectbox(
            "Age Range (optional)",
            ["Not specified", "Under 20", "20-30", "30-40", "40-50", "50+"],
            key="age_range_selector"
        )
    
    # Submit button
    st.markdown("---")
    
    if st.button("🚀 Get AI Skincare Recommendations", type="primary", use_container_width=True, key="submit_button"):
        
        # Validation using session state data
        if st.session_state.uploaded_file_data is None:
            st.error("❌ Please upload an image first!")
            return
        
        if goal_input == "Select your skincare goal":
            st.error("❌ Please select your skincare goal!")
            return
        
        if not history_input or history_input == ["Select products you've used"]:
            st.warning("⚠️ Adding product history will improve recommendations!")
            history_input = "No previous products mentioned"
        
        # Prepare history input
        history_text = history_input
        if isinstance(history_input, list):
            history_text = ", ".join(history_input)
        
        # Add additional info to history
        additional_info = []
        if skin_type != "Not specified":
            additional_info.append(f"Skin Type: {skin_type}")
        if age_range != "Not specified":
            additional_info.append(f"Age: {age_range}")
        
        if additional_info:
            if history_text == "No previous products mentioned":
                history_text = " | ".join(additional_info)
            else:
                history_text += " | " + " | ".join(additional_info)
        
        # Show loading
        with st.spinner("🔄 Analyzing your image and generating recommendations..."):
            # Progress bar for user experience
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            # Process the request using session state data
            result, error = process_skincare_request(st.session_state.uploaded_file_data, goal_input, history_text)
        
        # Clear progress bar
        progress_bar.empty()
        
        if error:
            st.error(f"❌ {error}")
        elif result:
            st.success("✅ Analysis complete!")
            display_results(result)
            
            # Download results option
            st.markdown("---")
            
            # Create downloadable content
            download_content = f"""
SKINCARE RECOMMENDATION REPORT
Generated by AI Skincare Recommendation System
Date: {time.strftime('%Y-%m-%d %H:%M:%S')}

═══════════════════════════════════════════════════════════════

📊 IMAGE ANALYSIS RESULTS:
• Brightness Score: {result['analysis']['brightness_score']}/255
• Brightness Level: {result['analysis']['brightness_level']}
• Processing Status: {'Success' if result['analysis']['image_processed'] else 'Failed'}

═══════════════════════════════════════════════════════════════

🎯 YOUR INPUT:
• Skincare Goal: {result['user_input']['goal']}
• Product History: {result['user_input']['history']}

═══════════════════════════════════════════════════════════════

💡 AI-POWERED RECOMMENDATIONS:
"""
            
            recommendation = result['recommendation']
            if isinstance(recommendation, dict):
                if 'routine' in recommendation:
                    download_content += f"\n🔄 RECOMMENDED ROUTINE:\n{recommendation['routine']}\n"
                if 'key_ingredients' in recommendation:
                    download_content += f"\n🧪 KEY INGREDIENTS TO LOOK FOR:\n{recommendation['key_ingredients']}\n"
                if 'avoid' in recommendation:
                    download_content += f"\n⚠️ PRODUCTS/INGREDIENTS TO AVOID:\n{recommendation['avoid']}\n"
                if 'timeline' in recommendation:
                    download_content += f"\n⏰ EXPECTED TIMELINE:\n{recommendation['timeline']}\n"
                if 'recommendation' in recommendation:
                    download_content += f"\n📝 AI GENERATED ADVICE:\n{recommendation['recommendation']}\n"
                    if 'source' in recommendation:
                        download_content += f"Source: {recommendation['source']}\n"
            else:
                download_content += f"\n{recommendation}\n"
            
            download_content += f"""
═══════════════════════════════════════════════════════════════

🛒 GET PREMIUM SKINCARE PRODUCTS:
Visit Dermatics India: https://dermatics.in/
Get premium skincare products delivered to your doorstep!

═══════════════════════════════════════════════════════════════

DISCLAIMER:
This is an AI-powered tool for educational purposes.
Always consult with a dermatologist for serious skin concerns.

Generated by AI Skincare Recommendation System
"""
            
            st.download_button(
                label="📥 Download Complete Results",
                data=download_content,
                file_name=f"skincare_recommendations_{int(time.time())}.txt",
                mime="text/plain",
                help="Download your complete skincare recommendation report",
                key="download_button"
            )
        else:
            st.error("❌ Unexpected error occurred. Please try again.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; padding: 20px;'>"
        "💡 This is an AI-powered tool for educational purposes. "
        "Always consult with a dermatologist for serious skin concerns."
        "</div>",
        unsafe_allow_html=True
    )

# Sample data for testing
def show_sample_data():
    st.markdown("### 🧪 Sample Test Data")
    
    with st.expander("Click to see sample inputs for testing"):
        st.markdown("**Sample Goals:**")
        st.code("""
        - "Brightening and evening skin tone"
        - "Anti-aging and wrinkle reduction"
        - "Acne treatment and oil control"
        - "Hydration for dry skin"
        - "Sensitive skin care routine"
        - "Pore minimization"
        - "Dark circles and under-eye care"
        """)
        
        st.markdown("**Sample Product History:**")
        st.code("""
        - "Vitamin C serum, Niacinamide serum, Sunscreen"
        - "Retinol products, Hyaluronic acid serum"
        - "Salicylic acid, Benzoyl peroxide treatments"
        - "Ceramide moisturizers, Gentle cleansers"
        """)

# Run the main app
if __name__ == "__main__":
    main()
    
    # Show sample data in sidebar
    with st.sidebar:
        st.markdown("---")
        show_sample_data()

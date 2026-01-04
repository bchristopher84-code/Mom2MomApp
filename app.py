import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file with GROK_API_KEY

GROK_API_URL = "https://api.x.ai/v1/chat/completions"
API_KEY = os.getenv("GROK_API_KEY")

def call_grok(prompt, use_search=False):
    messages = [{"role": "user", "content": prompt}]
    
    payload = {
        "model": "grok-4-1-fast-non-reasoning",  # Low-cost model
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 200  # Low for cost savings
    }
    
    if use_search:
        payload["search_parameters"] = {"mode": "on"}  # Enable web search for prices
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(GROK_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)} - Retry or check key/credits."

# Streamlit UI
st.title("Mom-to-Mom Sale Pricing Assistant")
st.markdown("Enter item details for short desc and price suggestions. Supports batches (comma-separated) and any category!")

category = st.selectbox("Item Category", ["Baby Clothes", "Toys", "Gear", "Books", "Other"])
condition = st.selectbox("Item Condition", ["New", "Like New", "Good", "Fair"])
brand = st.text_input("Brand (e.g., Carter's, or comma-separated for batch)")
size = st.text_input("Size (e.g., 6-12 months, or comma-separated)")
description = st.text_area("Description Idea (e.g., pink onesie with flowers, or comma-separated for batch)", height=100)
details = st.text_area("Additional Details (e.g., material, specs, or comma-separated)", height=100)

if st.button("Generate Suggestions") and description:
    # Support batch: Split inputs by comma
    brands = [b.strip() for b in brand.split(",") if b.strip()]
    sizes = [s.strip() for s in size.split(",") if s.strip()]
    descs = [d.strip() for d in description.split(",") if d.strip()]
    dets = [dt.strip() for dt in details.split(",") if dt.strip()]
    
    # Pad shorter lists to match longest
    max_len = max(len(brands), len(sizes), len(descs), len(dets))
    brands += [""] * (max_len - len(brands))
    sizes += [""] * (max_len - len(sizes))
    descs += [""] * (max_len - len(descs))
    dets += [""] * (max_len - len(dets))
    
    # Combined prompt for batch (one call)
    items_str = "; ".join([f"Item {i+1}: Brand '{brands[i]}', Size '{sizes[i]}', Desc '{descs[i]}', Details '{dets[i]}'" for i in range(max_len)])
    combined_prompt = f"For these {category} items in {condition} condition: {items_str}. For each, refine to a very short description (max 5 words). Then, research prices for similar new and used on sites like eBay, Facebook Marketplace, Amazon, Craigslist. Suggest competitive price range with 2-3 links. Output format: Item 1: Short Desc: [desc]\nPrice: [$X-Y explanation, links: link1, link2]\nItem 2: ..."
    combined_output = call_grok(combined_prompt, use_search=True)
    
    # Parse batch outputs
    st.subheader("Generated Suggestions")
    items = combined_output.split("Item ")
    for item in items[1:]:  # Skip first empty
        lines = item.split("\n")
        short_desc = lines[0].split("Short Desc:")[1].strip() if "Short Desc:" in lines[0] else "Short desc"
        price_suggestion = lines[1].split("Price:")[1].strip() if "Price:" in lines[1] else "Error"
        links = [word for word in price_suggestion.split() if word.startswith("http")]
        
        st.write(f"**Item {item.split(':')[0]}**")
        st.write("Short Description:", short_desc)
        st.write("Price Suggestion:", price_suggestion)
        if links:
            st.write("Sources:")
            for link in links:
                st.markdown(f"[View]({link})")
    
    if "Error" in combined_output:
        if st.button("Retry"):
            st.rerun()
    
    st.success("Copy to the sale website! (One API call used)")

# Sidebar cost tracker
if 'call_count' not in st.session_state:
    st.session_state.call_count = 0
st.session_state.call_count += 1
st.sidebar.write(f"API Calls This Session: {st.session_state.call_count} (~${st.session_state.call_count * 0.05})")

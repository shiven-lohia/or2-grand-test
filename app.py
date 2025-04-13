import streamlit as st
import pandas as pd
from dp_module import dp_packing
from ip_module import ip_packing
from preprocess_module import preprocess_csv

# --- Initialize session state ---
if 'show_results' not in st.session_state:
    st.session_state.show_results = False
if 'item_list' not in st.session_state:
    st.session_state.item_list = []

# --- Page 1: Method & Data Input ---
if not st.session_state.show_results:
    st.title("Optimal Packing Planner 📦")

    # 1) Choose method
    selected_mode = st.radio(
        "Select Packing Method:",
        ["Dynamic Programming", "Integer Programming", "DP + IP"]
    )
    st.session_state.selected_mode = selected_mode

    # Add the note below the DP/IP selection
    st.markdown(
        """
        <p style="font-size: 12px; opacity: 0.7;">
            ⚠️ <strong>Note:</strong> For Dynamic Programming (DP & DP+IP), the maximum number of items is 50, and the capacities are limited.
        </p>
        """,
        unsafe_allow_html=True
    )  

    # 2) Data input
    input_mode = st.radio("Select Input Method:", ["Upload CSV", "Add Items Manually"])
    df = None

    if input_mode == "Upload CSV":
        csv_file = st.file_uploader("Upload your CSV file", type=['csv'])
        if csv_file:
            raw_df = pd.read_csv(csv_file)
            df = preprocess_csv(raw_df)

            st.subheader("Movers Safety Preferences")
            cols = st.columns(3)
            movers_flags = []
            for idx, row in df.iterrows():
                col = cols[idx % 3]
                flag = col.checkbox(row['item'], value=True, key=f"mv_{idx}")
                movers_flags.append(flag)
            df['movers_safe'] = movers_flags

            st.write("Processed Data:")
            st.dataframe(df)

    else:
        value_mode = st.radio("Value Input Mode", ["Direct current value", "Compute from base value"])
        with st.form("add_item_form"):
            item = st.text_input("Item Name")
            weight = st.number_input("Weight (kg)", min_value=0.0, step=0.5)
            volume = st.number_input("Volume (L)", min_value=0.0, step=0.5)

            if value_mode == "Direct current value":
                current_value = st.number_input("Current Value (₹)", min_value=0, step=1, format="%d")
            else:
                mv = st.number_input("Monetary Value (₹)", min_value=0, step=1, format="%d")
                dep = st.number_input("Depreciation per year (%)", min_value=0, max_value=100, step=1, format="%d")
                age = st.number_input("Age (years)", min_value=0, step=1, format="%d")
                current_value = int(mv * (1 - dep/100) ** age)

            cabin_safe = st.checkbox("Cabin Safe")
            checkin_safe = st.checkbox("Check-in Safe")
            movers_safe = st.checkbox("Movers Safe", value=True)

            submitted = st.form_submit_button("Add Item")
            if submitted:
                if not (weight*2).is_integer() or not (volume*2).is_integer():
                    st.error("❌ Weight and Volume must be in 0.5 increments.")
                else:
                    st.session_state.item_list.append({
                        'item': item,
                        'weight': weight,
                        'volume': volume,
                        'current_value': current_value,
                        'cabin_safe': cabin_safe,
                        'checkin_safe': checkin_safe,
                        'movers_safe': movers_safe
                    })
                    # Avoid st.experimental_rerun, just update the page
                    st.session_state.show_results = False  # Reset results to show the input page
                    st.session_state.show_results = True  # Trigger page refresh with updated state

        if st.session_state.item_list:
            df = pd.DataFrame(st.session_state.item_list)
            st.write("Current Item List:")
            st.dataframe(df)

    # 3) Packing Configuration & Optimize button
    if df is not None and not df.empty:
        st.header("Packing Configuration")

        # Movers cost first
        movers_rate = st.number_input("Movers Cost per Volume (₹/L)", min_value=0.0, step=1.0)

        # Then capacities
        if selected_mode == "Integer Programming":
            col1, col2 = st.columns(2)
            with col1:
                cabin_weight = st.number_input("Cabin Max Weight (kg)", min_value=0, step=1, format="%d")
                cabin_volume = st.number_input("Cabin Max Volume (L)", min_value=0, step=1, format="%d")
            with col2:
                checkin_weight = st.number_input("Check-in Max Weight (kg)", min_value=0, step=1, format="%d")
                checkin_volume = st.number_input("Check-in Max Volume (L)", min_value=0, step=1, format="%d")
        else:
            col1, col2 = st.columns(2)
            with col1:
                cabin_weight = st.slider("Cabin Max Weight (kg)", 0, 7, 0)
                cabin_volume = st.slider("Cabin Max Volume (L)", 0, 45, 0)
            with col2:
                checkin_weight = st.slider("Check-in Max Weight (kg)", 0, 25, 0)
                checkin_volume = st.slider("Check-in Max Volume (L)", 0, 75, 0)

        # Save into session for results page
        st.session_state.df = df
        st.session_state.cabin_cap = {'max_weight': cabin_weight, 'max_volume': cabin_volume}
        st.session_state.checkin_cap = {'max_weight': checkin_weight, 'max_volume': checkin_volume}
        st.session_state.movers_rate = movers_rate

        if st.button("Optimize Packing"):
            st.session_state.show_results = True
            # Avoid rerun, but trigger the results page update
            st.session_state.show_results = True

# --- Page 2: Results ---
else:
    st.title("Packing Results 📊")

    df = st.session_state.df
    cabin_cap = st.session_state.cabin_cap
    checkin_cap = st.session_state.checkin_cap
    movers_rate = st.session_state.movers_rate
    selected_mode = st.session_state.selected_mode
    scale = 2
    choice_map = {0: 'Cabin', 1: 'Check-in', 2: 'Movers'}

    # DP section
    if selected_mode in ["Dynamic Programming", "DP + IP"]:
        with st.expander("📦 DP Packing Plan", expanded=False):
            with st.spinner("Computing DP solution..."):
                bs_dp, bv_dp, ba_dp = dp_packing(df, cabin_cap, checkin_cap, movers_rate, scale)

            df_dp = df.copy()
            df_dp['assignment'] = [choice_map[c] for c in ba_dp]

            st.success(f"DP Net Value: ₹{bv_dp:.2f}")
            st.write(f"• Cabin: W={round(bs_dp[0]/scale,2)}kg, V={round(bs_dp[1]/scale,2)}L")
            st.write(f"• Check-in: W={round(bs_dp[2]/scale,2)}kg, V={round(bs_dp[3]/scale,2)}L")
            st.dataframe(df_dp[['item','assignment']])

            st.markdown("**DP Assignment**")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**Cabin**")
                for it, asg in zip(df_dp['item'], df_dp['assignment']):
                    if asg == "Cabin":
                        st.write(f"• {it}")
            with c2:
                st.markdown("**Check-in**")
                for it, asg in zip(df_dp['item'], df_dp['assignment']):
                    if asg == "Check-in":
                        st.write(f"• {it}")
            with c3:
                st.markdown("**Movers**")
                for it, asg in zip(df_dp['item'], df_dp['assignment']):
                    if asg == "Movers":
                        st.write(f"• {it}")

    # IP section
    if selected_mode in ["Integer Programming", "DP + IP"]:
        with st.expander("📦 IP Packing Plan", expanded=False):
            with st.spinner("Computing IP solution..."):
                bs_ip, bv_ip, ba_ip = ip_packing(df, cabin_cap, checkin_cap, movers_rate)

            df_ip = df.copy()
            df_ip['assignment'] = ba_ip

            st.success(f"IP Net Value: ₹{bv_ip:.2f}")
            st.write(f"• Cabin: W={round(bs_ip[0],2)}kg, V={round(bs_ip[1],2)}L")
            st.write(f"• Check-in: W={round(bs_ip[2],2)}kg, V={round(bs_ip[3],2)}L")
            st.dataframe(df_ip[['item','assignment']])

            st.markdown("**IP Assignment**")
            d1, d2, d3 = st.columns(3)
            with d1:
                st.markdown("**Cabin**")
                for it, asg in zip(df_ip['item'], df_ip['assignment']):
                    if asg == "Cabin":
                        st.write(f"• {it}")
            with d2:
                st.markdown("**Check-in**")
                for it, asg in zip(df_ip['item'], df_ip['assignment']):
                    if asg == "Check-in":
                        st.write(f"• {it}")
            with d3:
                st.markdown("**Movers**")
                for it, asg in zip(df_ip['item'], df_ip['assignment']):
                    if asg == "Movers":
                        st.write(f"• {it}")

    # DP + IP comparison
    if selected_mode == "DP + IP":
        st.subheader("🔍 DP vs IP Comparison")
        comp_df = pd.DataFrame([
            {
                "Method": "DP",
                "Net Value (₹)": round(bv_dp, 2),
                "Cabin W Used (kg)": round(bs_dp[0]/scale, 2),
                "Check-in W Used (kg)": round(bs_dp[2]/scale, 2),
                "Cabin V Used (L)": round(bs_dp[1]/scale, 2),
                "Check-in V Used (L)": round(bs_dp[3]/scale, 2),
            },
            {
                "Method": "IP",
                "Net Value (₹)": round(bv_ip, 2),
                "Cabin W Used (kg)": round(bs_ip[0], 2),
                "Check-in W Used (kg)": round(bs_ip[2], 2),
                "Cabin V Used (L)": round(bs_ip[1], 2),
                "Check-in V Used (L)": round(bs_ip[3], 2),
            }
        ])
        st.table(comp_df.set_index("Method"))

    if st.button("← Back"):
        st.session_state.show_results = False
        # Avoid rerun and use session_state update to go back
        st.session_state.show_results = False

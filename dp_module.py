import pandas as pd

def dp_packing(df, cabin_cap, checkin_cap, cost_per_volume, scale=2):
    """
    Dynamic Programming solution with assignment tracking for packing problem.

    Parameters:
    - df: DataFrame with columns ['item', 'weight', 'volume', 'current_value', 'cabin_safe', 'checkin_safe', 'movers_safe']
    - cabin_cap: dict with keys 'max_weight', 'max_volume'
    - checkin_cap: dict with keys 'max_weight', 'max_volume'
    - cost_per_volume: cost charged by movers per liter
    - scale: multiplier to convert weights/volumes to integers (default 2 for 0.5 resolution)

    Returns:
    - best_state: tuple of used capacities (cabin_w, cabin_v, checkin_w, checkin_v)
    - best_value: maximum net value
    - best_assignments: list of assignment indices (0: cabin, 1: check-in, 2: movers)
    """
    W1 = int(cabin_cap['max_weight'] * scale)
    V1 = int(cabin_cap['max_volume'] * scale)
    W2 = int(checkin_cap['max_weight'] * scale)
    V2 = int(checkin_cap['max_volume'] * scale)

    states = {(0, 0, 0, 0): (0.0, [])}  # Initial state

    for idx, row in df.iterrows():
        w = int(row['weight'] * scale)
        v = int(row['volume'] * scale)
        val = row['current_value']
        mover_val = val - cost_per_volume * row['volume']  # unscaled volume

        new_states = dict(states)

        for (cw, cv, tw, tv), (acc_val, assign_list) in states.items():
            # Option 0: Cabin
            if row['cabin_safe'] and cw + w <= W1 and cv + v <= V1:
                key = (cw + w, cv + v, tw, tv)
                new_val = acc_val + val
                new_assign = assign_list + [0]
                if key not in new_states or new_val > new_states[key][0]:
                    new_states[key] = (new_val, new_assign)

            # Option 1: Check-in
            if row['checkin_safe'] and tw + w <= W2 and tv + v <= V2:
                key = (cw, cv, tw + w, tv + v)
                new_val = acc_val + val
                new_assign = assign_list + [1]
                if key not in new_states or new_val > new_states[key][0]:
                    new_states[key] = (new_val, new_assign)

            # Option 2: Movers
            if row['movers_safe']:
                key = (cw, cv, tw, tv)
                new_val = acc_val + mover_val
                new_assign = assign_list + [2]
                if key not in new_states or new_val > new_states[key][0]:
                    new_states[key] = (new_val, new_assign)

        states = new_states

    best_state, (best_value, best_assign) = max(states.items(), key=lambda kv: kv[1][0])
    return best_state, best_value, best_assign

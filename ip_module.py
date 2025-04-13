import pulp
import pandas as pd

def ip_packing(df, cabin_cap, checkin_cap, movers_rate):
    """
    Solves the packing problem using Integer Programming (IP) and returns:
    - net value
    - used capacities
    - assignment list
    """

    # Define problem
    model = pulp.LpProblem("PackingOptimization", pulp.LpMaximize)

    # Decision variables
    x_cabin = pulp.LpVariable.dicts('cabin', df.index, cat='Binary')
    x_checkin = pulp.LpVariable.dicts('checkin', df.index, cat='Binary')
    x_mover = pulp.LpVariable.dicts('mover', df.index, cat='Binary')

    # Objective: Maximize total net value
    model += pulp.lpSum(
        df.loc[i, 'current_value'] * (x_cabin[i] + x_checkin[i]) +
        (df.loc[i, 'current_value'] - movers_rate * df.loc[i, 'volume']) * x_mover[i]
        for i in df.index
    )

    # Constraint: Each item must be assigned exactly once
    for i in df.index:
        model += x_cabin[i] + x_checkin[i] + x_mover[i] == 1

    # Capacity constraints
    model += pulp.lpSum(df.loc[i, 'weight'] * x_cabin[i] for i in df.index) <= cabin_cap['max_weight']
    model += pulp.lpSum(df.loc[i, 'volume'] * x_cabin[i] for i in df.index) <= cabin_cap['max_volume']
    model += pulp.lpSum(df.loc[i, 'weight'] * x_checkin[i] for i in df.index) <= checkin_cap['max_weight']
    model += pulp.lpSum(df.loc[i, 'volume'] * x_checkin[i] for i in df.index) <= checkin_cap['max_volume']

    # Safety constraints
    for i in df.index:
        if not df.loc[i, 'cabin_safe']:
            model += x_cabin[i] == 0
        if not df.loc[i, 'checkin_safe']:
            model += x_checkin[i] == 0
        if not df.loc[i, 'movers_safe']:
            model += x_mover[i] == 0

    # Solve
    model.solve(pulp.PULP_CBC_CMD(msg=False))

    # Extract assignments
    assignment = []
    for i in df.index:
        if pulp.value(x_cabin[i]) == 1:
            assignment.append('Cabin')
        elif pulp.value(x_checkin[i]) == 1:
            assignment.append('Check-in')
        else:
            assignment.append('Movers')

    # Calculate used capacities
    used_cabin_w = sum(df.loc[i, 'weight'] for i in df.index if assignment[i] == 'Cabin')
    used_cabin_v = sum(df.loc[i, 'volume'] for i in df.index if assignment[i] == 'Cabin')
    used_check_w = sum(df.loc[i, 'weight'] for i in df.index if assignment[i] == 'Check-in')
    used_check_v = sum(df.loc[i, 'volume'] for i in df.index if assignment[i] == 'Check-in')
    net_value = pulp.value(model.objective)

    used_state = (used_cabin_w, used_cabin_v, used_check_w, used_check_v)

    return used_state, net_value, assignment

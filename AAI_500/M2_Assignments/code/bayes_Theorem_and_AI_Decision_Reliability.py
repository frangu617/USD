# Bayes' Theorem and AI Decision Reliability

P_target = 0.03
P_alert_given_target = 0.95
P_alert_given_no_target = 0.10

P_no_target = 1 - P_target

# Probability of any alert: correct alerts plus false alarms
P_alert = (
    P_alert_given_target * P_target
    + P_alert_given_no_target * P_no_target
)

# Probability a target is present, given an alert
P_target_given_alert = (
    P_alert_given_target * P_target
) / P_alert

print(f"Probability of an alert: {P_alert:.2%}")
print(f"Probability of a target given an alert: {P_target_given_alert:.2%}")

# Interpretation:
# When the AI raises an alert, there is about a 22.71% chance
# that a target is actually present. That means about 77.29%
# of alerts are false alarms. Although the AI detects 95% of
# actual targets, targets are uncommon, so false alarms from
# areas without targets outnumber the correct alerts.


# Bonus: change the probabilities and calculate the updated result
def bayes_posterior(p_target, p_alert_given_target, p_alert_given_no_target):
    p_alert = (
        p_alert_given_target * p_target
        + p_alert_given_no_target * (1 - p_target)
    )

    if p_alert == 0:
        raise ValueError("The posterior is undefined when alerts cannot occur.")

    return (p_alert_given_target * p_target) / p_alert

# Let the user enter new probabilities.
print("\nEnter probabilities between 0 and 1.")
print("For example, enter 0.03 for 3%.")

try:
    p_target = float(input("Probability of a target: "))
    p_detection = float(input("Probability of an alert when a target is present: "))
    p_false_alarm = float(input("Probability of an alert when no target is present: "))

    if not all(0 <= p <= 1 for p in (p_target, p_detection, p_false_alarm)):
        raise ValueError("Each probability must be between 0 and 1.")

    result = bayes_posterior(p_target, p_detection, p_false_alarm)
    print(f"\nProbability of a target given an alert: {result:.2%}")

except ValueError as error:
    print(f"Invalid input: {error}")
bonus_result = bayes_posterior(0.005, 0.95, 0.10)
print(f"Probability of a target given an alert when prevalence is 0.5%: {bonus_result:.2%}")

# When targets become even rarer, the chance that an alert is
# correct drops from about 22.71% to 4.56%, even though the
# AI's detection and false-alarm rates stay the same.
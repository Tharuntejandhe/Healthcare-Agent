from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server for Medical Tools
mcp = FastMCP("MedicalSpecialist")

@mcp.tool()
def check_drug_interaction(drug_a: str, drug_b: str) -> str:
    """Checks for potential interactions between two medications."""
    # Simplified mock interaction logic
    interactions = {
        ("aspirin", "warfarin"): "High Risk: Increased risk of bleeding.",
        ("ibuprofen", "lisinopril"): "Moderate Risk: May reduce the effectiveness of lisinopril.",
        ("metformin", "alcohol"): "High Risk: Risk of lactic acidosis."
    }
    
    pair = tuple(sorted([drug_a.lower(), drug_b.lower()]))
    return interactions.get(pair, "No common interactions found in local database. Please consult a pharmacist.")

@mcp.tool()
def calculate_cardiac_risk(age: int, systolic_bp: int, smoker: bool) -> str:
    """Calculates a simplified 10-year cardiac risk score."""
    score = (age * 0.1) + (systolic_bp * 0.05)
    if smoker:
        score += 5
    
    if score > 15:
        return f"Risk Score: {score:.1f} (High Risk). Immediate lifestyle intervention recommended."
    return f"Risk Score: {score:.1f} (Normal Risk). Continue healthy habits."

if __name__ == "__main__":
    mcp.run()

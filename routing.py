# backend/app/routing.py

ROUTING_TABLE = {
    "Water Supply": {"dept_code": "WTR-001", "contact": "water_dept@example.gov"},
    "Sanitation": {"dept_code": "SAN-002", "contact": "sanitation_dept@example.gov"},
    "Electricity": {"dept_code": "ELC-003", "contact": "electricity_dept@example.gov"},
    "Roads & Infrastructure": {"dept_code": "RD-004", "contact": "roads_dept@example.gov"},
    "Health & Safety": {"dept_code": "HLT-005", "contact": "health_dept@example.gov"},
    "Public Transport": {"dept_code": "PT-006", "contact": "transport_dept@example.gov"},
    "General Administration": {"dept_code": "ADM-999", "contact": "admin_dept@example.gov"},
}

def route_to_department(department_name: str) -> str:
    info = ROUTING_TABLE.get(department_name, ROUTING_TABLE["General Administration"])
    # In the prototype we return "<dept_code> - <contact>"
    return f"{info['dept_code']} | {info['contact']}"

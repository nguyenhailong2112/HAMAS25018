# HAMAS25018 Documentation Index

Bo tai lieu nay la chuan trien khai cho Vision Server HAMAS25018.

Main concept:

```text
AI Camera Vision Server
  -> Detect Slot Status
  -> Generate Occupancy State
  -> WebSocket Push
  -> Tablet / Caller App
  -> User Validate
  -> Tablet POST task to FMS
```

Vision Server chi dong vai tro state provider. Vision khong tao task, khong goi FMS va khong dieu phoi AGV/FMR.

## Thu Tu Doc

1. [01_project_spec.md](01_project_spec.md) - Scope va vai tro Vision Server.
2. [02_system_architecture.md](02_system_architecture.md) - Main concept process va kien truc.
3. [03_data_contract_api.md](03_data_contract_api.md) - Data contract API/WebSocket.
4. [04_config_spec.md](04_config_spec.md) - Config camera/slot/ROI.
5. [05_migration_scope.md](05_migration_scope.md) - Scope tinh gon tu core cu.
6. [06_cpu_runtime_plan.md](06_cpu_runtime_plan.md) - Runtime CPU-only 6 camera.
7. [07_testing_acceptance.md](07_testing_acceptance.md) - Test plan va acceptance.
8. [08_deployment_operations.md](08_deployment_operations.md) - Deployment/operation.
9. [09_risk_register.md](09_risk_register.md) - Risk register.
10. [10_implementation_backlog.md](10_implementation_backlog.md) - Backlog.
11. [11_checkpoint_plan.md](11_checkpoint_plan.md) - Checkpoint plan.
12. [12_operation_runbook.md](12_operation_runbook.md) - Runbook khoi dong nhanh.
13. [13_current_state_report.md](13_current_state_report.md) - Bao cao hien trang.
14. [14_integration_handoff.md](14_integration_handoff.md) - Handoff API ngan gon.
15. [15_site_communication_guide.md](15_site_communication_guide.md) - Huong dan ket noi tai site cho Tablet/FMS/network team.

## Contract Cot Loi

Payload WebSocket/REST:

```json
{
  "timestamp": "2026-06-23T09:00:00.000+07:00",
  "total_slots": 22,
  "slots": [
    {
      "camera_id": "cam1",
      "slot_id": "S1",
      "state": "Occupied"
    }
  ]
}
```

State public:

- `Empty`: slot khong co hang.
- `Occupied`: slot co hang.
- `Unknown`: Vision chua du chac chan hoac pipeline/camera dang loi.

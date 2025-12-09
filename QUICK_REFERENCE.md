# Quick Reference Card

## Files Overview

```
/Users/visubramaniam/ansible-array-restore/
├── storage_provisioning_generator.py      # Python script to generate playbooks
├── STORAGE_PROVISIONING_GUIDE.md          # Complete usage guide (THIS FILE)
├── generated_playbooks/
│   ├── 00_complete_provisioning_workflow.yml    # ⭐ Recommended: All-in-one
│   ├── 01_create_storage_pool.yml               # Storage pool only
│   ├── 02_create_ddp_pool.yml                   # DDP pool only
│   ├── 03_create_ldevs.yml                      # LDEVs only
│   ├── 04_create_hostgroup.yml                  # Hostgroup only
│   ├── 05_provision_ldevs_to_hostgroup.yml      # Provisioning only
│   └── README.md                                # Playbook documentation
└── all_storage_facts.json                 # Input source data
```

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────┐
│    Storage Provisioning Workflow                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Storage Pool       Create HDP pool              │
│     ├─→ [Pool ID]                                  │
│                                                     │
│  2. DDP Pool           Create dynamic pool          │
│     ├─→ [DDP Pool ID]                              │
│                                                     │
│  3. LDEVs              Create volumes               │
│     ├─→ [LDEV IDs: 100, 101]                       │
│                                                     │
│  4. Hostgroup          Create connectivity group    │
│     ├─→ [Hostgroup Created]                        │
│                                                     │
│  5. Provision LDEVs    Mount volumes to hosts       │
│     └─→ [Provisioning Complete]                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Fast Start Commands

### 1️⃣ Setup (One-Time)
```bash
# Install collection
ansible-galaxy collection install hitachivantara.vspone_block

# Create vault file with your credentials
cat > ansible_vault_vars/ansible_vault_storage_var.yml << 'EOF'
storage_address: "192.168.1.100"
vault_storage_username: "admin"
vault_storage_secret: "your_password"
EOF
```

### 2️⃣ Run Complete Provisioning
```bash
cd generated_playbooks
ansible-playbook 00_complete_provisioning_workflow.yml
```

### 3️⃣ Verify Success
```bash
# Check playbook execution results
tail -20 provisioning.log

# Query storage facts for new resources
jq '.storage_pools.ansible_facts.storage_pool[-1]' all_storage_facts.json
```

---

## Command Variations

| Task | Command |
|------|---------|
| **All-in-one** | `ansible-playbook 00_complete_provisioning_workflow.yml` |
| **Dry run** | `ansible-playbook 00_complete_provisioning_workflow.yml --check` |
| **Debug output** | `ansible-playbook 00_complete_provisioning_workflow.yml -vvv` |
| **Custom pool name** | `ansible-playbook ... -e "pool_config.name=my_pool"` |
| **Custom port** | `ansible-playbook ... -e "hostgroup_config.port=CL2-A"` |
| **Custom capacity** | `ansible-playbook ... -e "pool_config.capacity=200GB"` |
| **Windows host mode** | `ansible-playbook ... -e "hostgroup_config.host_mode=WINDOWS"` |
| **With tags** | `ansible-playbook ... --tags=pool,ldev` |
| **Skip DDP pool** | `ansible-playbook ... --skip-tags=ddp_pool` |
| **Run specific playbook** | `ansible-playbook 03_create_ldevs.yml` |
| **Save output** | `ansible-playbook ... | tee output.log` |

---

## Available Storage Ports
```
CL1-A  CL2-A  CL3-A  CL4-A  CL5-A  CL6-A  CL7-A  CL8-A
```

## Host Modes
```
LINUX           WINDOWS         WINDOWS_EXTENSION
AIX             HP-UX           SOLARIS
LINUX_LEGACY    VMWARE          OVMS
```

## Capacity Saving Options
```
none                          # No optimization
compression                   # Compression only
deduplication                 # Deduplication only
compression_deduplication     # Both (recommended)
```

---

## Key Variables Cheat Sheet

```yaml
# Connection (Required)
storage_address: "192.168.x.x"
vault_storage_username: "admin"
vault_storage_secret: "password"

# Pool Settings
pool_config:
  name: "my_pool"
  capacity: "50GB"
  parity_group_id: "1-1"          # Available: 1-1, E1-1, E1-4, etc.

# LDEV Settings
ldev_config:
  - name: "volume1"
    size: "50GB"
    capacity_saving: "compression_deduplication"
    data_reduction_share: true

# Hostgroup Settings
hostgroup_config:
  name: "servers"
  port: "CL1-A"                   # Available: CL1-A to CL8-A
  host_mode: "LINUX"
  wwns: ["50:00:1fe1:0001:0000:0001:0000:0001"]

# Provisioning
provisioning_config:
  hostgroup_name: "servers"
  ldev_ids: [100, 101]            # IDs from LDEV creation
```

---

## Troubleshooting Quick Fix

| Issue | Solution |
|-------|----------|
| **Connection failed** | Check storage_address, verify network connectivity |
| **Authentication failed** | Verify username/password in vault file |
| **Port not found** | Choose from CL1-A to CL8-A (use `ls -l all_storage_facts.json` to verify) |
| **Insufficient capacity** | Check parity group capacity in all_storage_facts.json |
| **LDEV creation failed** | Verify pool_id exists and has free space |
| **Hostgroup already exists** | Change hostgroup_config.name to unique value |
| **Provisioning failed** | Verify ldev_ids exist and hostgroup exists |

---

## Extract Information from Facts

```bash
# List all parity groups
jq '.parity_groups.ansible_facts.parity_groups[] | {id: .parity_group_id, capacity: .total_capacity}' all_storage_facts.json

# List all storage pools
jq '.storage_pools.ansible_facts.storage_pool[] | {id: .pool_id, name: .pool_name, status: .pool_status}' all_storage_facts.json

# List all hostgroups
jq '.host_groups.ansible_facts.hostGroups[] | {name: .host_group_name, port: .port_id, mode: .host_mode}' all_storage_facts.json

# Find available ports
jq '.host_groups.ansible_facts.hostGroups[].port_id' all_storage_facts.json | sort -u
```

---

## Example Scenarios

### Scenario 1: Small Development Environment
```bash
ansible-playbook 00_complete_provisioning_workflow.yml \
  -e "pool_config.name=dev_pool" \
  -e "pool_config.capacity=10GB" \
  -e "ldev_config=[
    {name: 'dev_app', size: '5GB', capacity_saving: 'compression', data_reduction_share: true}
  ]"
```

### Scenario 2: Production Database
```bash
ansible-playbook 00_complete_provisioning_workflow.yml \
  -e "pool_config.name=prod_database" \
  -e "pool_config.capacity=500GB" \
  -e "ldev_config=[
    {name: 'data_volume', size: '300GB', capacity_saving: 'compression_deduplication', data_reduction_share: true},
    {name: 'log_volume', size: '100GB', capacity_saving: 'none', data_reduction_share: false},
    {name: 'backup_volume', size: '200GB', capacity_saving: 'compression_deduplication', data_reduction_share: true}
  ]" \
  -e "hostgroup_config.host_mode=WINDOWS"
```

### Scenario 3: Multi-Host Cluster
```bash
ansible-playbook 00_complete_provisioning_workflow.yml \
  -e "pool_config.name=cluster_pool" \
  -e "hostgroup_config.wwns=[
    '50:00:1fe1:0001:0000:0001:0000:0010',
    '50:00:1fe1:0001:0000:0001:0000:0011',
    '50:00:1fe1:0001:0000:0001:0000:0012'
  ]"
```

---

## Performance Tips

1. **Use compression_deduplication** for better space efficiency
2. **Set data_reduction_share: true** to maximize dedup efficiency
3. **Monitor thresholds** - set warning at 70%, depletion at 80%
4. **Use separate pools** for different workload types
5. **Check parity group capacity** before pool creation

---

## Next Steps

1. ✅ Review STORAGE_PROVISIONING_GUIDE.md
2. ✅ Customize variables in playbooks
3. ✅ Run `ansible-playbook --check` for dry run
4. ✅ Execute main playbook
5. ✅ Verify resources created
6. ✅ Configure hosts to discover volumes

---

**Quick Links:**
- [Complete Guide](STORAGE_PROVISIONING_GUIDE.md)
- [Playbook README](generated_playbooks/README.md)
- [Hitachi VSP Docs](https://www.hitachi.com/products/it/storage/)

---

**Last Updated:** December 9, 2025

# Storage Provisioning Solution - Complete Guide

## Overview

This solution provides a Python script and auto-generated Ansible playbooks to automate the creation of Hitachi VSP storage resources. The script reads your existing storage facts (from `all_storage_facts.json`) and generates ready-to-use Ansible playbooks for:

1. **Storage Pool Creation** - HDP (Hitachi Dynamic Provisioning) pools for traditional storage
2. **DDP Pool Creation** - Dynamic Drive Pools with encryption and auto-drive assignment
3. **LDEV Creation** - Logical Devices with compression and deduplication
4. **Hostgroup Creation** - Storage connectivity groups for host access
5. **LDEV Provisioning** - Mounting LDEVs to hostgroups for host access

---

## Files Generated

### Python Generator Script
- **`storage_provisioning_generator.py`** - Main Python script that:
  - Reads `all_storage_facts.json`
  - Extracts storage configuration data
  - Generates 6 Ansible playbooks
  - Creates comprehensive README

### Generated Playbooks

#### 1. **Complete Workflow** (Recommended)
- **File:** `00_complete_provisioning_workflow.yml`
- **Purpose:** Creates all resources in proper sequence
- **Resources Created:**
  - Storage Pool (HDP type)
  - DDP Pool
  - 2 LDEVs (database_volume: 50GB, app_volume: 100GB)
  - Hostgroup
  - Provisions both LDEVs to the hostgroup

#### 2. **Individual Playbooks** (Modular)
- `01_create_storage_pool.yml` - Storage pool creation only
- `02_create_ddp_pool.yml` - DDP pool creation only
- `03_create_ldevs.yml` - LDEV creation only
- `04_create_hostgroup.yml` - Hostgroup creation only
- `05_provision_ldevs_to_hostgroup.yml` - LDEV provisioning only

#### 3. **Documentation**
- `README.md` - Complete usage guide and reference

---

## Extracted Storage Configuration

From your `all_storage_facts.json`, the generator identified:

| Resource | Count | Details |
|----------|-------|---------|
| Parity Groups | 14 | Primary: 1-1, External: E1-1, E1-4, E1-5, E2-1, E2-2, etc. |
| Storage Pools | 3 | Main pool: DC1-B28-B-Main-Pool (92.37TB, 16% used) |
| Hostgroups | 76 | Across 8 storage ports |
| Storage Ports | 8 | CL1-A, CL2-A, CL3-A, CL4-A, CL5-A, CL6-A, CL7-A, CL8-A |
| LDEVs (Sample) | 36+ | Total capacity: ~96TB |

---

## Quick Start

### 1. Prerequisites Setup

```bash
# Install Hitachi VSP Collection
ansible-galaxy collection install hitachivantara.vspone_block

# Create vault variables file
cat > ansible_vault_vars/ansible_vault_storage_var.yml << 'EOF'
storage_address: "192.168.x.x"
vault_storage_username: "admin"
vault_storage_secret: "your_password"
EOF
```

### 2. Run Complete Workflow

```bash
cd generated_playbooks
ansible-playbook 00_complete_provisioning_workflow.yml
```

### 3. Customize Configuration

Edit playbook variables:

```bash
ansible-playbook 00_complete_provisioning_workflow.yml \
  -e "pool_config.name=my_custom_pool" \
  -e "pool_config.capacity=100GB" \
  -e "hostgroup_config.name=my_servers" \
  -e "hostgroup_config.port=CL2-A"
```

---

## Detailed Usage Guide

### Option A: Complete Workflow (Recommended for First-Time)

Best for creating an entire storage infrastructure in one execution:

```bash
ansible-playbook 00_complete_provisioning_workflow.yml
```

**What it does:**
1. Creates storage pool on parity group 1-1
2. Creates DDP pool with encryption enabled
3. Creates 2 LDEVs: database_volume (50GB) and app_volume (100GB)
4. Creates hostgroup on port CL1-A with LINUX host mode
5. Provisions both LDEVs to the hostgroup

**Expected Output:**
```
TASK [Create Storage Pool] ****
ok: [localhost] => ...
storage_pool_id: 1

TASK [Create DDP Pool] ****
ok: [localhost] => ...
ddp_pool_id: 2

TASK [Create LDEVs] ****
ok: [localhost] => ...
created_ldev_ids: [100, 101]

TASK [Create Hostgroup] ****
ok: [localhost] => ...

TASK [Provision LDEVs to Hostgroup] ****
ok: [localhost] => ...

PLAY RECAP ****
localhost : ok=15 changed=5 unreachable=0 failed=0
```

---

### Option B: Individual Playbooks (For Modular Control)

Run each playbook separately:

#### Step 1: Create Storage Pool
```bash
ansible-playbook 01_create_storage_pool.yml
```

**Output:**
- Variable: `created_pool_id`
- Use this ID for LDEV creation

#### Step 2: Create DDP Pool
```bash
ansible-playbook 02_create_ddp_pool.yml
```

**Output:**
- Variable: `created_ddp_pool_id`
- Optional: Use for separate storage tier

#### Step 3: Create LDEVs
```bash
ansible-playbook 03_create_ldevs.yml \
  -e "pool_id=1"  # Use pool ID from Step 1
```

**Output:**
- Variable: `created_ldev_ids` = [100, 101, ...]
- Save these IDs for provisioning

#### Step 4: Create Hostgroup
```bash
ansible-playbook 04_create_hostgroup.yml \
  -e "hostgroup_config.port=CL2-A"  # Choose available port
```

**Output:**
- Created hostgroup ready for LDEV attachment

#### Step 5: Provision LDEVs
```bash
ansible-playbook 05_provision_ldevs_to_hostgroup.yml \
  -e "provisioning_config.ldev_ids=[100,101]"  # Use IDs from Step 3
```

**Output:**
- LDEVs now accessible to hosts connected to hostgroup

---

## Customization Examples

### Example 1: Large Database Storage
```bash
ansible-playbook 00_complete_provisioning_workflow.yml \
  -e "pool_config.name=database_pool" \
  -e "pool_config.capacity=500GB" \
  -e "ldev_config=[
    {name: 'db_data', size: '200GB', capacity_saving: 'compression_deduplication', data_reduction_share: true},
    {name: 'db_logs', size: '100GB', capacity_saving: 'none', data_reduction_share: false},
    {name: 'db_backup', size: '300GB', capacity_saving: 'compression_deduplication', data_reduction_share: true}
  ]" \
  -e "hostgroup_config.name=database_servers"
```

### Example 2: Windows Environment
```bash
ansible-playbook 00_complete_provisioning_workflow.yml \
  -e "hostgroup_config.host_mode=WINDOWS" \
  -e "hostgroup_config.wwns=[
    '50:00:1fe1:0001:0000:0001:0000:0010',
    '50:00:1fe1:0001:0000:0001:0000:0011',
    '50:00:1fe1:0001:0000:0001:0000:0012'
  ]"
```

### Example 3: AIX System
```bash
ansible-playbook 00_complete_provisioning_workflow.yml \
  -e "hostgroup_config.host_mode=AIX" \
  -e "pool_config.name=aix_pool" \
  -e "hostgroup_config.port=CL3-A"
```

### Example 4: Dry Run (Check Mode)
```bash
ansible-playbook 00_complete_provisioning_workflow.yml --check
```

---

## Advanced: Using Specific Tags

Run only specific resource creation:

```bash
# Create pool only
ansible-playbook 00_complete_provisioning_workflow.yml --tags=pool

# Create and provision LDEVs (skip pool/DDP creation)
ansible-playbook 00_complete_provisioning_workflow.yml --tags=ldev,provision

# Skip DDP pool creation
ansible-playbook 00_complete_provisioning_workflow.yml --skip-tags=ddp_pool
```

---

## Variable Reference

### Connection Info
```yaml
connection_info:
  address: "192.168.x.x"          # Storage management IP
  username: "admin"               # Admin user
  password: "your_password"       # Admin password (from vault)
```

### Pool Configuration
```yaml
pool_config:
  name: "pool_name"               # Pool name
  pool_type: "HDP"                # HDP or DDP
  parity_group_id: "1-1"          # Parity group
  capacity: "50GB"                # Pool size
  warning_threshold: 70           # Warning at 70% full
  depletion_threshold: 80         # Error at 80% full
```

### DDP Pool Configuration
```yaml
ddp_pool_config:
  name: "ddp_pool"                # DDP pool name
  is_encryption_enabled: true     # Enable encryption
  threshold_warning: 70           # Warning threshold
  threshold_depletion: 80         # Depletion threshold
```

### LDEV Configuration
```yaml
ldev_config:
  - name: "volume_name"           # Volume name
    size: "50GB"                  # Volume size
    capacity_saving: "compression_deduplication"  # Options: none, compression, deduplication, compression_deduplication
    data_reduction_share: true    # Share reduction across volumes
```

### Hostgroup Configuration
```yaml
hostgroup_config:
  name: "hostgroup_name"          # Hostgroup name
  port: "CL1-A"                   # Storage port
  host_mode: "LINUX"              # Host OS: LINUX, WINDOWS, AIX, SOLARIS, etc.
  wwns:
    - "50:00:1fe1:0001:0000:0001:0000:0001"  # Host WWN identifiers
    - "50:00:1fe1:0001:0000:0001:0000:0002"
```

### Provisioning Configuration
```yaml
provisioning_config:
  hostgroup_name: "hostgroup_name"    # Target hostgroup
  port: "CL1-A"                       # Storage port
  ldev_ids: [100, 101, 102]           # LDEV IDs to provision
```

---

## Common Operations

### Scale Volumes
To add more volumes after initial creation:

```bash
ansible-playbook 03_create_ldevs.yml \
  -e "pool_id=1" \
  -e "ldev_config=[
    {name: 'new_volume_1', size: '100GB', capacity_saving: 'compression_deduplication', data_reduction_share: true},
    {name: 'new_volume_2', size: '150GB', capacity_saving: 'compression_deduplication', data_reduction_share: true}
  ]"
```

### Add More Hosts
```bash
ansible-playbook 04_create_hostgroup.yml \
  -e "hostgroup_config.name=additional_servers" \
  -e "hostgroup_config.port=CL2-A" \
  -e "hostgroup_config.wwns=['50:00:1fe1:0001:0000:0001:0000:0020']"
```

### Provision Additional LDEVs to Existing Hostgroup
```bash
ansible-playbook 05_provision_ldevs_to_hostgroup.yml \
  -e "provisioning_config.hostgroup_name=existing_hostgroup" \
  -e "provisioning_config.ldev_ids=[103,104]"
```

---

## Troubleshooting

### Connection Issues
```bash
# Test connectivity
ping <storage_address>

# Verify credentials
ansible -i localhost, all -m debug -a "var=storage_address" --ask-vault-pass
```

### Verify Storage Facts
```bash
# View available parity groups
jq '.parity_groups.ansible_facts.parity_groups' all_storage_facts.json

# View available ports
jq '.host_groups.ansible_facts.hostGroups[].port_id' all_storage_facts.json | sort -u

# View storage pools
jq '.storage_pools.ansible_facts.storage_pool[] | {pool_id, pool_name, pool_status}' all_storage_facts.json
```

### Debug Mode
```bash
ansible-playbook 00_complete_provisioning_workflow.yml -vvv
```

---

## Regenerating Playbooks

To regenerate playbooks with updated storage facts:

```bash
# Update storage facts
ansible-playbook gather_all_facts.yml  # Your facts gathering playbook

# Regenerate playbooks
python3 storage_provisioning_generator.py /path/to/all_storage_facts.json ./new_playbooks
```

---

## Security Considerations

1. **Use Ansible Vault for passwords:**
   ```bash
   ansible-vault create ansible_vault_vars/ansible_vault_storage_var.yml
   ```

2. **Restrict file permissions:**
   ```bash
   chmod 600 ansible_vault_vars/ansible_vault_storage_var.yml
   ```

3. **Use SSH keys for Ansible:**
   ```bash
   ansible-playbook playbook.yml --private-key=/path/to/key
   ```

4. **Audit operations:**
   ```bash
   ansible-playbook playbook.yml -e "ansible_verbosity=3" | tee provisioning.log
   ```

---

## Support & Resources

- **Hitachi VSP Collection:** https://github.com/hitachi-vantara/vspone-block-ansible
- **Ansible Documentation:** https://docs.ansible.com
- **Hitachi Support:** https://www.hitachi.com/products/it/storage/support

---

## Change Log

### v1.0 (Initial Release)
- Python generator script for playbook creation
- 6 Ansible playbooks (1 combined + 5 individual)
- Automatic storage facts analysis
- Comprehensive documentation

---

**Generated:** December 9, 2025
**Storage System:** Hitachi VSP
**Ansible Collection:** hitachivantara.vspone_block

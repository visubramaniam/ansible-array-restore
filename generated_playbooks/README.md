# Storage Provisioning Playbooks

Auto-generated Ansible playbooks for Hitachi VSP storage provisioning.

## Generated Playbooks

### 1. Complete Workflow (Recommended)
**File:** `00_complete_provisioning_workflow.yml`

This playbook creates all resources in sequence:
1. Creates a Storage Pool
2. Creates a DDP Pool
3. Creates LDEVs (Logical Devices)
4. Creates a Hostgroup
5. Provisions LDEVs to the Hostgroup

**Usage:**
```bash
ansible-playbook 00_complete_provisioning_workflow.yml
```

### 2. Individual Playbooks

#### Storage Pool
**File:** `01_create_storage_pool.yml`

Creates a storage pool using available parity groups.

**Usage:**
```bash
ansible-playbook 01_create_storage_pool.yml
```

**Variables:**
- `pool_config.name`: Pool name (default: "ansible_managed_pool")
- `pool_config.size`: Pool capacity (default: "50GB")
- `pool_config.parity_group_id`: Parity group to use

#### DDP Pool
**File:** `02_create_ddp_pool.yml`

Creates a DDP (Dynamic Drive Pool) pool.

**Usage:**
```bash
ansible-playbook 02_create_ddp_pool.yml
```

**Variables:**
- `ddp_pool_config.name`: Pool name (default: "ansible_ddp_pool")
- `ddp_pool_config.is_encryption_enabled`: Enable encryption (default: true)

#### LDEVs
**File:** `03_create_ldevs.yml`

Creates logical devices (LDEVs) in the specified pool.

**Usage:**
```bash
ansible-playbook 03_create_ldevs.yml -e "pool_id=0"
```

**Variables:**
- `pool_id`: Target pool ID (default: 0)
- `ldev_config`: List of LDEV configurations

Each LDEV configuration includes:
```yaml
- name: "volume_name"
  size: "50GB"
  capacity_saving: "compression_deduplication"
  data_reduction_share: true
```

#### Hostgroup
**File:** `04_create_hostgroup.yml`

Creates a hostgroup for connecting hosts to storage.

**Usage:**
```bash
ansible-playbook 04_create_hostgroup.yml
```

**Variables:**
- `hostgroup_config.name`: Hostgroup name (default: "ansible_hostgroup")
- `hostgroup_config.port`: Storage port (default: "CL1-A")
- `hostgroup_config.host_mode`: Host OS type (default: "LINUX")
- `hostgroup_config.wwns`: List of host WWN identifiers

#### Provisioning
**File:** `05_provision_ldevs_to_hostgroup.yml`

Provisions (presents) LDEVs to a hostgroup.

**Usage:**
```bash
ansible-playbook 05_provision_ldevs_to_hostgroup.yml \
  -e "provisioning_config.ldev_ids=[1,2,3]"
```

**Variables:**
- `provisioning_config.hostgroup_name`: Target hostgroup
- `provisioning_config.port`: Storage port
- `provisioning_config.ldev_ids`: List of LDEV IDs to provision

## Prerequisites

1. **Hitachi VSP One Ansible Collection**
   ```bash
   ansible-galaxy collection install hitachivantara.vspone_block
   ```

2. **Vault Variables File**
   Create `ansible_vault_vars/ansible_vault_storage_var.yml` with:
   ```yaml
   storage_address: "192.168.x.x"
   vault_storage_username: "admin"
   vault_storage_secret: "password"
   ```

3. **Network Access**
   - Connectivity to Hitachi VSP storage management interface

## Execution Examples

### Run Complete Workflow
```bash
ansible-playbook 00_complete_provisioning_workflow.yml
```

### Run with Custom Variables
```bash
ansible-playbook 00_complete_provisioning_workflow.yml \
  -e "pool_config.name=custom_pool" \
  -e "hostgroup_config.name=custom_hostgroup"
```

### Run Specific Tags
```bash
# Create pool only
ansible-playbook 00_complete_provisioning_workflow.yml --tags=pool

# Create and provision LDEVs only
ansible-playbook 00_complete_provisioning_workflow.yml --tags=ldev,provision
```

### Run in Check Mode (Dry Run)
```bash
ansible-playbook 00_complete_provisioning_workflow.yml --check
```

## Variables Override

You can override any variables using `-e` flag:

```bash
ansible-playbook 00_complete_provisioning_workflow.yml \
  -e "pool_config.name=my_pool" \
  -e "pool_config.capacity=100GB" \
  -e "hostgroup_config.port=CL2-B" \
  -e "hostgroup_config.host_mode=WINDOWS"
```

## Storage Configuration from Facts

These playbooks were generated from your existing storage facts data:

### Identified Resources
- **Parity Groups**: Available for pool creation
- **Storage Ports**: CL1-A, CL1-B, CL2-A, CL2-B, etc.
- **Existing Pools**: {len(self.get_storage_pools())} pools found
- **Existing Hostgroups**: {len(self.get_hostgroups())} hostgroups found

### Default Settings
- **Default Port**: {self.get_storage_ports()[0] if self.get_storage_ports() else 'CL1-A'}
- **Default Parity Group**: {self.get_available_parity_group() or '1-1'}
- **Default Host Mode**: LINUX

## Customization

To customize the playbooks:

1. Edit variable sections in the playbooks
2. Modify `ldev_config` to add more volumes
3. Update `hostgroup_config` with your host WWNs
4. Adjust capacity and performance parameters as needed

## Troubleshooting

### Common Issues

1. **Connection Failures**
   - Verify storage address and credentials
   - Check network connectivity to storage management interface

2. **Insufficient Capacity**
   - Check available capacity in parity groups
   - Reduce requested pool/LDEV sizes

3. **Port Unavailable**
   - Verify port ID exists (use storage_port.yml facts)
   - Ensure port is not in use or reserved

4. **Host Mode Mismatch**
   - Verify host_mode matches your environment:
     - LINUX, WINDOWS, WINDOWS_EXTENSION, AIX, etc.

## Additional Resources

- [Hitachi VSP Collection Documentation](https://github.com/hitachi-vantara/vspone-block-ansible)
- [VSP Storage System Documentation](https://www.hitachi.com/products/it/storage/)

---

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

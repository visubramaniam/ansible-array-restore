# Storage Provisioning - Ansible Role Structure

This document shows how to convert the generated playbooks into a reusable Ansible role.

## Directory Structure for Ansible Role

```
roles/
└── storage_provisioning/
    ├── defaults/
    │   └── main.yml                    # Default variables
    ├── tasks/
    │   ├── main.yml                    # Main task orchestrator
    │   ├── create_pool.yml             # Pool creation tasks
    │   ├── create_ddp_pool.yml         # DDP pool tasks
    │   ├── create_ldevs.yml            # LDEV creation tasks
    │   ├── create_hostgroup.yml        # Hostgroup tasks
    │   └── provision_ldevs.yml         # Provisioning tasks
    ├── vars/
    │   └── main.yml                    # Role variables
    ├── handlers/
    │   └── main.yml                    # Handlers for notifications
    ├── templates/
    │   └── storage_config.j2           # Configuration templates
    └── README.md                        # Role documentation
```

## Implementation

### 1. Create Role Structure

```bash
mkdir -p roles/storage_provisioning/{defaults,tasks,vars,handlers}
```

### 2. defaults/main.yml

```yaml
---
# Default variables for storage_provisioning role

# Connection settings (override in inventory)
storage_address: "192.168.1.100"
storage_username: "admin"
storage_password: "password"

# Pool configuration defaults
pool_config:
  name: "default_pool"
  pool_type: "HDP"
  parity_group_id: "1-1"
  capacity: "50GB"
  warning_threshold: 70
  depletion_threshold: 80
  state: present

# DDP pool configuration defaults
ddp_pool_config:
  name: "default_ddp_pool"
  is_encryption_enabled: true
  threshold_warning: 70
  threshold_depletion: 80
  state: present

# LDEV configuration defaults
ldev_config:
  - name: "database_volume"
    size: "50GB"
    capacity_saving: "compression_deduplication"
    data_reduction_share: true
  - name: "app_volume"
    size: "100GB"
    capacity_saving: "compression_deduplication"
    data_reduction_share: true

# Hostgroup configuration defaults
hostgroup_config:
  name: "default_hostgroup"
  port: "CL1-A"
  host_mode: "LINUX"
  wwns:
    - "50:00:1fe1:0001:0000:0001:0000:0001"
  state: present

# Provisioning configuration defaults
provisioning_config:
  hostgroup_name: "default_hostgroup"
  port: "CL1-A"
  ldev_ids: []
  state: present

# Feature flags
create_pool: true
create_ddp_pool: true
create_ldevs: true
create_hostgroup: true
provision_ldevs: true

# Debugging
enable_debug: false
```

### 3. vars/main.yml

```yaml
---
# Variables specific to storage_provisioning role

# Internal connection info
connection_info:
  address: "{{ storage_address }}"
  username: "{{ storage_username }}"
  password: "{{ storage_password }}"

# Status tracking
provisioning_results: {}
created_resources: {}
```

### 4. tasks/main.yml

```yaml
---
# Main tasks for storage_provisioning role

- name: Storage Provisioning Role
  block:
    - name: Create storage pool
      include_tasks: create_pool.yml
      when: create_pool | bool

    - name: Create DDP pool
      include_tasks: create_ddp_pool.yml
      when: create_ddp_pool | bool

    - name: Create LDEVs
      include_tasks: create_ldevs.yml
      when: create_ldevs | bool

    - name: Create hostgroup
      include_tasks: create_hostgroup.yml
      when: create_hostgroup | bool

    - name: Provision LDEVs to hostgroup
      include_tasks: provision_ldevs.yml
      when: provision_ldevs | bool and (created_ldev_ids is defined)

    - name: Display provisioning summary
      debug:
        msg: |
          ==========================================
          Storage Provisioning Summary
          ==========================================
          Pool Created: {{ pool_config.name }}
          DDP Pool Created: {{ ddp_pool_config.name }}
          LDEVs Created: {{ created_ldev_ids | default([]) | length }}
          Hostgroup Created: {{ hostgroup_config.name }}
          Provisioning Status: Success
          ==========================================
  rescue:
    - name: Handle provisioning errors
      debug:
        msg: "Provisioning failed: {{ ansible_failed_result }}"
      when: enable_debug | bool
```

### 5. tasks/create_pool.yml

```yaml
---
# Storage pool creation tasks

- name: Create Storage Pool
  hitachivantara.vspone_block.vsp.hv_storagepool:
    connection_info: "{{ connection_info }}"
    state: "{{ pool_config.state }}"
    spec:
      pool_name: "{{ pool_config.name }}"
      pool_type: "{{ pool_config.pool_type }}"
      parity_group_id: "{{ pool_config.parity_group_id }}"
      capacity: "{{ pool_config.capacity }}"
      warning_threshold: "{{ pool_config.warning_threshold }}"
      depletion_threshold: "{{ pool_config.depletion_threshold }}"
  register: pool_result

- name: Set pool ID fact
  set_fact:
    created_pool_id: "{{ pool_result['pool']['pool_id'] }}"
  when: pool_result is succeeded

- name: Display pool creation result
  debug:
    msg: "Storage Pool created: {{ pool_config.name }} (ID: {{ created_pool_id }})"
  when: pool_result is succeeded and enable_debug | bool
```

### 6. tasks/create_ddp_pool.yml

```yaml
---
# DDP pool creation tasks

- name: Create DDP Pool
  hitachivantara.vspone_block.vsp.hv_ddp_pool:
    connection_info: "{{ connection_info }}"
    state: "{{ ddp_pool_config.state }}"
    spec:
      pool_name: "{{ ddp_pool_config.name }}"
      is_encryption_enabled: "{{ ddp_pool_config.is_encryption_enabled }}"
      threshold_warning: "{{ ddp_pool_config.threshold_warning }}"
      threshold_depletion: "{{ ddp_pool_config.threshold_depletion }}"
  register: ddp_pool_result

- name: Set DDP pool ID fact
  set_fact:
    created_ddp_pool_id: "{{ ddp_pool_result['pool']['pool_id'] }}"
  when: ddp_pool_result is succeeded

- name: Display DDP pool creation result
  debug:
    msg: "DDP Pool created: {{ ddp_pool_config.name }} (ID: {{ created_ddp_pool_id }})"
  when: ddp_pool_result is succeeded and enable_debug | bool
```

### 7. tasks/create_ldevs.yml

```yaml
---
# LDEV creation tasks

- name: Create LDEVs
  hitachivantara.vspone_block.vsp.hv_ldev:
    connection_info: "{{ connection_info }}"
    state: present
    spec:
      pool_id: "{{ created_pool_id | default(0) }}"
      size: "{{ item.size }}"
      name: "{{ item.name }}"
      capacity_saving: "{{ item.capacity_saving }}"
      data_reduction_share: "{{ item.data_reduction_share }}"
  register: ldev_result
  loop: "{{ ldev_config }}"
  loop_control:
    label: "{{ item.name }}"

- name: Collect LDEV IDs
  set_fact:
    created_ldev_ids: "{{ ldev_result.results | map(attribute='volume.ldev_id') | list }}"
  when: ldev_result is succeeded

- name: Display LDEV creation results
  debug:
    msg: |
      LDEVs created: {{ created_ldev_ids | length }}
      IDs: {{ created_ldev_ids }}
  when: ldev_result is succeeded and enable_debug | bool
```

### 8. tasks/create_hostgroup.yml

```yaml
---
# Hostgroup creation tasks

- name: Create Hostgroup
  hitachivantara.vspone_block.vsp.hv_hg:
    connection_info: "{{ connection_info }}"
    state: "{{ hostgroup_config.state }}"
    spec:
      name: "{{ hostgroup_config.name }}"
      port: "{{ hostgroup_config.port }}"
      host_mode: "{{ hostgroup_config.host_mode }}"
  register: hostgroup_result

- name: Display hostgroup creation result
  debug:
    msg: "Hostgroup created: {{ hostgroup_config.name }} on port {{ hostgroup_config.port }}"
  when: hostgroup_result is succeeded and enable_debug | bool

- name: Add WWNs to hostgroup
  hitachivantara.vspone_block.vsp.hv_hg:
    connection_info: "{{ connection_info }}"
    state: present
    spec:
      state: add_wwn
      name: "{{ hostgroup_config.name }}"
      port: "{{ hostgroup_config.port }}"
      wwns: "{{ hostgroup_config.wwns }}"
  register: add_wwn_result
  when: hostgroup_config.wwns | length > 0
```

### 9. tasks/provision_ldevs.yml

```yaml
---
# LDEV provisioning tasks

- name: Provision LDEVs to Hostgroup
  hitachivantara.vspone_block.vsp.hv_hg:
    connection_info: "{{ connection_info }}"
    state: present
    spec:
      state: present_ldev
      name: "{{ provisioning_config.hostgroup_name }}"
      port: "{{ provisioning_config.port }}"
      ldevs: "{{ created_ldev_ids | default(provisioning_config.ldev_ids) }}"
  register: provision_result
  when: (created_ldev_ids is defined and created_ldev_ids | length > 0) or (provisioning_config.ldev_ids | length > 0)

- name: Display provisioning result
  debug:
    msg: |
      LDEVs provisioned to {{ provisioning_config.hostgroup_name }}
      Count: {{ (created_ldev_ids | default(provisioning_config.ldev_ids)) | length }}
  when: provision_result is succeeded and enable_debug | bool
```

### 10. handlers/main.yml

```yaml
---
# Handlers for storage_provisioning role

- name: Verify provisioning
  debug:
    msg: "Provisioning verification completed"
  listen: "verify provisioning"
```

### 11. README.md

```markdown
# storage_provisioning Role

Ansible role for automating Hitachi VSP storage provisioning.

## Role Variables

All variables are defined in `defaults/main.yml` and can be overridden.

### Required Variables
- `storage_address`: Storage management IP
- `storage_username`: Admin username
- `storage_password`: Admin password

### Pool Configuration
- `pool_config.name`: Pool name
- `pool_config.capacity`: Pool size (e.g., "50GB")
- `pool_config.parity_group_id`: Parity group ID

### Feature Flags
- `create_pool`: Create storage pool (default: true)
- `create_ddp_pool`: Create DDP pool (default: true)
- `create_ldevs`: Create LDEVs (default: true)
- `create_hostgroup`: Create hostgroup (default: true)
- `provision_ldevs`: Provision LDEVs (default: true)

## Usage Examples

### Basic Usage
```yaml
- hosts: localhost
  roles:
    - storage_provisioning
```

### With Custom Variables
```yaml
- hosts: localhost
  roles:
    - role: storage_provisioning
      vars:
        pool_config:
          name: "custom_pool"
          capacity: "100GB"
        hostgroup_config:
          name: "production_servers"
```

### Selective Features
```yaml
- hosts: localhost
  roles:
    - role: storage_provisioning
      vars:
        create_pool: true
        create_ddp_pool: false
        create_ldevs: true
        create_hostgroup: true
        provision_ldevs: true
```

## Facts Generated
- `created_pool_id`: ID of created storage pool
- `created_ddp_pool_id`: ID of created DDP pool
- `created_ldev_ids`: List of LDEV IDs created

## Dependencies
- hitachivantara.vspone_block collection

## License
Apache 2.0
```

## Usage Example Playbook

```yaml
---
# playbook.yml - Using storage_provisioning role

- name: Storage Provisioning with Role
  hosts: localhost
  gather_facts: false

  vars_files:
    - ansible_vault_vars/ansible_vault_storage_var.yml

  vars:
    # Override defaults
    pool_config:
      name: "production_pool"
      capacity: "500GB"
      parity_group_id: "1-1"
    
    hostgroup_config:
      name: "production_servers"
      port: "CL2-A"
      host_mode: "LINUX"
      wwns:
        - "50:00:1fe1:0001:0000:0001:0000:0010"
        - "50:00:1fe1:0001:0000:0001:0000:0011"

  roles:
    - storage_provisioning
```

## Running the Role

```bash
# Run with defaults
ansible-playbook playbook.yml

# Run with verbose output
ansible-playbook playbook.yml -vv

# Run specific tag
ansible-playbook playbook.yml --tags="pool"

# Dry run
ansible-playbook playbook.yml --check
```

---

## Comparison: Playbooks vs Role

| Aspect | Generated Playbooks | Ansible Role |
|--------|-------------------|--------------|
| **Reusability** | Low (single use) | High (multiple projects) |
| **Customization** | Via CLI variables | Via role variables |
| **Organization** | Flat structure | Modular structure |
| **Defaults** | Hardcoded | Centralized in defaults/ |
| **Complexity** | Simpler | More structured |
| **Scaling** | Limited | Excellent |

---

**Recommendation:** Use generated playbooks for quick prototyping, convert to role structure for production use.

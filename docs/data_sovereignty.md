# Data Sovereignty Options

- [Data Sovereignty Options](#data-sovereignty-options)
  - [Executive summary](#executive-summary)
  - [1 The three approaches, in plain terms](#1-the-three-approaches-in-plain-terms)
    - [1.1 On‑prem](#11-onprem)
    - [1.2 Public cloud with third‑party-provided certifications](#12-public-cloud-with-thirdparty-provided-certifications)
    - [1.3 Public cloud with CPU TEE and GPU TEE](#13-public-cloud-with-cpu-tee-and-gpu-tee)
  - [2 Technical comparison](#2-technical-comparison)
    - [2.1 Trust model](#21-trust-model)
    - [2.2 What is actually protected](#22-what-is-actually-protected)
    - [2.3 Architecture and operational constraints](#23-architecture-and-operational-constraints)
    - [2.4 Performance and engineering friction](#24-performance-and-engineering-friction)
  - [3 Business comparison](#3-business-comparison)
    - [3.1 Procurement and auditability](#31-procurement-and-auditability)
    - [3.2 Time to value](#32-time-to-value)
    - [3.3 Strategic flexibility](#33-strategic-flexibility)
  - [4 Financial comparison](#4-financial-comparison)
    - [4.1 Cost structure](#41-cost-structure)
    - [4.2 Hidden costs](#42-hidden-costs)
    - [4.3 Pricing nuance](#43-pricing-nuance)
  - [5 Side-by-side conclusion](#5-side-by-side-conclusion)
    - [Best choice if your priority is…](#best-choice-if-your-priority-is)
    - [Practical decision rule](#practical-decision-rule)
  - [6 Recommendation for most enterprise evaluations](#6-recommendation-for-most-enterprise-evaluations)
  - [Sources](#sources)

## Executive summary

When it comes to Data Sovereignty, different approache are available.

If primary requirement is **maximum (physical) control and bespoke security architecture**, **on‑prem** is still the strongest option, but it comes with the highest operational burden, the slowest scaling, and the heaviest capital commitment. It is best when you already operate mature infrastructure/security teams, have hard sovereignty constraints, or need deep customization at the hardware/network layer.

If your primary requirement is **regulatory evidence, procurement acceptability, and lower operational overhead**, **public cloud backed by third‑party certifications** is often the easiest route. Providers such as OVHcloud publish broad portfolios of certifications and compliance attestations (for example ISO 27001/27017/27018, ISO 27701, SOC 1/2/3, GDPR alignment, PCI DSS, HIPAA/HITECH, SecNumCloud, HDS, EBA, C5, ENS, etc.), which materially help with vendor due diligence and regulated procurement. However, certifications mainly demonstrate that controls and processes were assessed by auditors—they do **not** by themselves provide cryptographic protection of data **while it is being processed**. 

If your primary requirement is **minimizing trust in the cloud operator for data‑in‑use**, **public cloud with CPU TEE (and, for AI workloads, GPU TEE)** is the strongest cloud-native confidential-computing pattern. Azure and Google Cloud both expose VM-level TEE options based on **AMD SEV‑SNP** and/or **Intel TDX**, with attestation and no-code-change lift‑and‑shift support for many workloads; Google [1] and Spheron [2] are examples of providers offering such services. This is the best fit when you need cloud elasticity *and* a materially stronger technical trust model than “the provider passed an audit.”

[1]: https://www.spheron.network/ "Spheron"
[2]: https://www.spheron.network/ "Spheron"

---

## 1 The three approaches, in plain terms

### 1.1 On‑prem

This means you buy/lease and operate the infrastructure yourself: servers, storage, networking, power, cooling, monitoring, patching, incident response, capacity planning, DR, and audit evidence. The upside is full control over architecture, procurement, geographic placement, and operational procedures. The downside is that you own the entire security and availability burden, and you must fund capacity before you need it.

**Confidential-computing implication:** on‑prem can absolutely use TEE-capable hardware too, but the comparison category here is mainly about the **deployment/control model**: you trust your own administrators and facilities more than a cloud operator, and you accept the operational trade-off that comes with that.

### 1.2 Public cloud with third‑party-provided certifications

This model relies on conventional cloud infrastructure plus evidence that the provider has undergone audits and attained recognized certifications or attestations. OVHcloud’s compliance page is a good example: it emphasizes independent auditors, security management certifications, regional/legal commitments, and sector-specific frameworks for healthcare, finance, and public sector use cases. citeturn1search1

**Confidential-computing implication:** certifications improve your ability to satisfy governance, audit, legal, and procurement requirements; they reduce the burden of proving that the provider has documented controls. But they do **not** fundamentally change the runtime trust boundary the way hardware TEE does.

### 1.3 Public cloud with CPU TEE and GPU TEE

This model uses **hardware-enforced trusted execution environments** so that data remains protected **while in use**. Google documents that Confidential VMs use hardware-based memory encryption, with keys residing in dedicated hardware and inaccessible to the hypervisor, plus attestation to verify the VM/platform state before secrets are released. Azure documents similar capabilities with confidential VM families backed by **AMD SEV‑SNP** and **Intel TDX**; Azure also exposes a confidential GPU-enabled H100 VM family. Google further documents confidential GPU-capable Confidential VMs on supported machine types. 

**Important nuance:** not every cloud uses the same model. On AWS, **Nitro Enclaves** are an enclave-based confidential-computing primitive, not the same thing as a “full confidential VM” model. Nitro Enclaves provide highly constrained isolated environments with no external networking, no persistent storage, and attestation; AWS also offers **NitroTPM** for measured boot and attestation. That is powerful, but architecturally different from Azure/Google’s full-VM CPU TEE offerings. 

---

## 2 Technical comparison

### 2.1 Trust model

- **On‑prem:** strongest control over the *people, place, and platform*. Your organization controls physical access, admin paths, network segmentation, logging, HSM placement, and lifecycle. This is the most direct way to reduce exposure to third-party operators, but it assumes your own admins and processes are the trust anchor.
- **Certified public cloud:** trust is primarily **contractual, procedural, and audited**. Certifications show that the provider’s controls were evaluated by independent assessors and mapped to recognized frameworks, which is valuable for assurance and procurement. But the provider’s hypervisor/admin/control-plane trust assumptions remain broadly conventional. citeturn1search1
- **CPU/GPU TEE public cloud:** trust shifts toward **hardware-rooted isolation and attestation**. Google explicitly states that Confidential VMs use hardware-based memory encryption with keys inaccessible to the hypervisor and that attestation can verify identity/state; Azure similarly positions confidential VMs as TEEs using AMD SEV‑SNP or Intel TDX. This materially narrows the trusted computing base compared with a certification-only cloud model. citeturn1search18turn1search17turn1search26

### 2.2 What is actually protected

- **On‑prem:** you can protect data at rest, in transit, and—if you deploy the right hardware/software stack—also data in use. But that protection is your responsibility to design and operate.
- **Certified public cloud:** excellent for proving control maturity, governance, residency commitments, and sector-readiness; not sufficient by itself for protecting **data in use** from the infrastructure layer. OVH’s page, for example, highlights auditors, compliance, and sector certifications rather than hardware attestation-based runtime isolation. citeturn1search1
- **CPU TEE cloud:** protects VM memory/state during execution with hardware isolation and attestation. Google and Azure document AMD SEV‑SNP / Intel TDX support and note that many workloads can be lifted and shifted without code changes. citeturn1search18turn1search17turn1search26
- **GPU TEE cloud:** extends the TEE boundary to the accelerator for AI/ML scenarios. Google explicitly says NVIDIA confidential computing can extend a TEE to include a GPU; Azure exposes an H100 confidential GPU VM family. This matters when sensitive prompts, embeddings, fine-tuning data, model weights, or inference results would otherwise leave the protected CPU boundary once sent to the GPU. citeturn1search18turn1search17turn1search33

### 2.3 Architecture and operational constraints

- **On‑prem:** most flexible architecture, but you must build HA/DR, patching, attestation tooling, key management, and incident response yourself.
- **Certified public cloud:** operationally simplest of the three if your security model is satisfied by standard cloud controls plus audits.
- **CPU/GPU TEE cloud:** strongest technical cloud posture, but with more constraints. Google documents supported machine types, OS images, and live-migration limitations; for example, some confidential VM/GPU combinations have specific image requirements and may not support live migration. Azure similarly notes region-specific availability and that confidential VMs resize only within confidential-capable families. citeturn1search33turn1search17
- **AWS enclave model:** excellent for isolating narrowly scoped sensitive functions (key handling, tokenization, highly sensitive transformations), but the enclave model is intentionally constrained: no SSH, no external networking, no persistent storage, and communication only with the parent instance. That is a feature for security, but it changes application architecture. citeturn1search4

### 2.4 Performance and engineering friction

- **On‑prem:** performance is predictable if you size correctly, but you pay for idle capacity and must refresh hardware yourself.
- **Certified public cloud:** usually lowest engineering friction because you run on standard instance types and standard service patterns.
- **CPU TEE cloud:** performance overhead is workload dependent. Google states AMD SEV on Confidential VM can range from no noticeable difference to minimal overhead depending on workload; academic measurement on AMD SEV also found near-zero impact for CPU-heavy work, modest impact for memory-sensitive work, but potentially much higher penalties on disk/network-heavy workloads in some cases. In practice, that means TEE is often fine for many compute workloads, but I/O-heavy or latency-sensitive systems still need benchmarking. citeturn1search18turn1search31
- **GPU TEE cloud:** adds even more deployment specificity (supported OS/machine/GPU stacks), so it is best reserved for workloads that truly need confidential AI rather than as a default for all GPU use. Google documents that confidential GPU support sits on supported configurations such as A3/H100. citeturn1search18turn1search33

---

## 3 Business comparison

### 3.1 Procurement and auditability

- **On‑prem:** easiest to explain when the business wants direct ownership and explicit control, but hardest to evidence at scale because you must produce and maintain all control documentation yourself.
- **Certified public cloud:** strongest choice when the business driver is “get through vendor risk, legal, internal audit, and regulated procurement faster.” OVHcloud’s compliance portfolio is a clear example of how providers package trust evidence for healthcare, finance, public sector, and regional sovereignty narratives. citeturn1search1
- **TEE cloud:** best when business leadership needs to say not only *“the provider is audited”* but also *“the provider’s infrastructure cannot trivially inspect our workload memory while it is running.”* That is a meaningfully stronger story for high-sensitivity datasets, multi-party analytics, and confidential AI. citeturn1search18turn1search26

### 3.2 Time to value

- **On‑prem:** slowest. Procurement, installation, network integration, DR planning, and security baselining take time.
- **Certified public cloud:** fastest for conventional workloads and regulated projects that do not require in-use cryptographic isolation.
- **TEE cloud:** slower than standard cloud because of compatibility testing, attestation integration, image selection, and platform constraints—but still far faster than building equivalent capability on-prem from scratch. Azure and Google both present confidential VMs as deployable managed offerings rather than bespoke hardware projects. citeturn1search17turn1search18

### 3.3 Strategic flexibility

- **On‑prem:** best for sovereign control and bespoke architectures, worst for elastic scaling and rapid experimentation.
- **Certified public cloud:** best for broad service catalogs, geographic expansion, and standard DevSecOps workflows.
- **TEE cloud:** strongest for organizations that want cloud agility without fully trusting provider operators for data-in-use. It is especially compelling for cross-organization data sharing, regulated analytics, and confidential AI/ML pipelines. Google explicitly frames confidential computing as enabling collaboration while retaining data ownership/confidentiality. citeturn1search18turn1search33

---

## 4 Financial comparison

### 4.1 Cost structure

- **On‑prem:** highest **CapEx** and longest commitment horizon. You pay upfront for servers, racks, storage, network gear, spares, support contracts, facilities overhead, and staffing. This can be economically attractive only when utilization is high and stable enough to amortize the asset base well.
- **Certified public cloud:** mostly **OpEx**, easier to start, easier to scale down, and easier to allocate by project/business unit. Financially, this is usually the cleanest option for uncertain demand or growing workloads because you avoid large upfront purchases.
- **TEE cloud:** still largely OpEx, but with potentially higher unit costs than standard cloud because you are using specialized confidential instance families and, in the GPU case, accelerator-backed instances. Azure documents dedicated confidential VM families and an H100 confidential GPU family; Google documents specific supported confidential machine families, including GPU-backed confidential configurations. citeturn1search17turn1search33

### 4.2 Hidden costs

- **On‑prem hidden costs:** underutilization, refresh cycles, spare capacity, audit preparation, DR duplication, and the ongoing salary cost of skilled platform/security operators.
- **Certified public cloud hidden costs:** egress, observability sprawl, compliance evidence mapping across services, and potential lock-in around managed services.
- **TEE cloud hidden costs:** compatibility testing, performance validation, limited SKU/region/OS options, and the engineering work to integrate attestation and key-release policies correctly. Google and Azure both document platform-specific support matrices and limitations; AWS enclaves require application partitioning around the enclave model. citeturn1search33turn1search17turn1search4

### 4.3 Pricing nuance

A useful nuance is that **some confidential-computing features do not necessarily introduce a separate line-item fee**. AWS explicitly states there is **no additional charge** for Nitro Enclaves or NitroTPM beyond the underlying resources used. That does **not** mean the total solution is cheap—it means the cost is embedded in the selected EC2 footprint and surrounding services rather than in a separate “confidential computing surcharge.” citeturn1search4turn1search8

---

## 5 Side-by-side conclusion

### Best choice if your priority is…

- **Absolute control / sovereignty / custom architecture:** **On‑prem**
- **Fastest path through audit, procurement, and sector compliance:** **Public cloud with third-party certifications**
- **Strongest technical protection for cloud data-in-use:** **Public cloud with CPU TEE**
- **Strongest technical protection for confidential AI/ML:** **Public cloud with CPU TEE + GPU TEE**

### Practical decision rule

Choose **on‑prem** if the organization is willing to fund and operate a serious infrastructure/security program in exchange for control.

Choose **certified public cloud** if your main question is **“Can this provider satisfy our auditors, regulators, and procurement team?”**

Choose **CPU/GPU TEE public cloud** if your main question is **“How do we reduce trust in the provider/operator while keeping cloud elasticity?”** That is the most directly aligned answer to confidential computing as a technical security objective. citeturn1search1turn1search18turn1search17

---

## 6 Recommendation for most enterprise evaluations

For most enterprises comparing “confidential computing” options today, the most balanced strategy is:

1. **Use certifications/compliance as the procurement and governance baseline**, because they remain necessary for audit, vendor risk, and regulated industry acceptance. citeturn1search1
2. **Use CPU TEE for genuinely sensitive workloads that must run in public cloud**, because it changes the runtime trust model rather than merely documenting process controls. citeturn1search18turn1search17turn1search26
3. **Use GPU TEE only for AI/ML workloads where the data/model risk justifies accelerator-confidentiality constraints and cost.** citeturn1search18turn1search17turn1search33
4. **Keep on‑prem only where sovereignty, custom hardware control, or predictable high utilization outweigh the operational drag.**

In one sentence: **certifications prove process maturity, TEEs provide technical runtime isolation, and on‑prem provides ownership/control; the right answer depends on which of those three you value most.**

---

## Sources

- OVHcloud compliance and certification overview: https://www.ovhcloud.com/en/compliance/
- Azure Confidential VM options: https://learn.microsoft.com/en-us/azure/confidential-computing/virtual-machine-options
- Azure Confidential VM FAQ: https://learn.microsoft.com/en-us/azure/confidential-computing/confidential-vm-faq
- Google Cloud Confidential VM overview: https://docs.cloud.google.com/confidential-computing/confidential-vm/docs/confidential-vm-overview
- Google Cloud Confidential VM supported configurations: https://docs.cloud.google.com/confidential-computing/confidential-vm/docs/supported-configurations
- AWS Nitro Enclaves: https://docs.aws.amazon.com/enclaves/latest/user/nitro-enclave.html
- AWS NitroTPM: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/nitrotpm.html
- Academic reference on CVM overheads: https://kartikgopalan.github.io/publications/mascots23.pdf

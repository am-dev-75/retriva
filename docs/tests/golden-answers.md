# Benchmark QAs

# KB: https://wiki.dave.eu/

1. What is the maximum power consumption of AURA SOM?

Based on the provided context, there is no single explicit "maximum power consumption" specification (e.g., a rated P_max) listed for the AURA SOM in the text snippets. However, measured power consumption values from various operational modes and stress tests are documented in the image descriptions within the **AURA SOM/AURA Hardware/pdf** source.

According to these measurements:
*   **Stress Conditions:** Under stress conditions (specifically the `AURA_power_a55_stress_OD` test), the maximum observed power consumption is approximately **2.75 W to 2.8 W** [10]. Other stress tests (`AURA_power_a55_stress_ND` and `AURA_power_a55_stress_LD`) show maximums around **2.15 W** and **2.0 W**, respectively [10].
*   **Idle Conditions:** In idle states, peak power can reach approximately **2.2 W** (e.g., `AURA_power_a55_idle_OD`), with average idle power typically around **1.5 W to 1.7 W** [10].
*   **Low Power Modes:** In low-power idle modes (`AURA_power_lp_idle`), consumption is around **0.6 W**. In suspend mode (`AURA_power_lp_suspend`), it drops to approximately **0.16 W**, and in BBSM mode (`AURA_power_lp_bbsm`), it is approximately **1.10 mW** [10].

The AURA SOM is based on the i.MX93 SoC, which supports innovative power management [1]. While a specific theoretical maximum rating is not provided in the text, the highest measured value in the provided stress test data is approximately **2.8 W**.

*Note: A separate source titled "Thermal tests and measurements (SBCX)" mentions a maximum of 3.8 W, but the context does not explicitly confirm that the SBCX board uses the AURA SOM, so this value is not attributed to AURA in the provided text.*

Sources:
[1] AURA SOM/AURA Hardware/Power modes - DAVE Developer's Wiki
[2] AURA SOM/AURA Hardware/Electrical Thermal and Mechanical Features/Operational characteristics - DAVE Developer's Wiki
[3] AURA SOM/AURA Hardware/Electrical Thermal and Mechanical Features/Mechanical specifications - DAVE Developer's Wiki
[4] AURA SOM/AURA Hardware/General Information/Processor and memory subsystem - DAVE Developer's Wiki
[5] AURA SOM/AURA Hardware/Part number composition - DAVE Developer's Wiki
[6] AURA SOM/AURA Hardware/Peripherals/Real Time Clock - DAVE Developer's Wiki
[7] AURA SOM/AURA Hardware/Electrical Thermal and Mechanical Features/Thermal management and heat dissipation - DAVE Developer's Wiki
[8] AURA SOM/AURA Hardware/Peripherals/LCD - DAVE Developer's Wiki
[9] AURA SOM/AURA Hardware/Peripherals/Audio - DAVE Developer's Wiki
[10] AURA SOM/AURA Hardware/pdf - DAVE Developer's Wiki
[11] AURA SOM/AURA Hardware/Peripherals/LVDS - DAVE Developer's Wiki
[12] AURA SOM/AURA Hardware/Peripherals/UART - DAVE Developer's Wiki
[13] AURA SOM/AURA Hardware/Power and Reset/JTAG - DAVE Developer's Wiki
[14] AURA SOM/AURA Hardware/Peripherals/SDIO - DAVE Developer's Wiki
[15] AURA SOM/AURA Hardware/Peripherals/CAN - DAVE Developer's Wiki
[16] AURA SOM/AURA Hardware/Peripherals/Watchdog - DAVE Developer's Wiki
[17] AURA SOM/AURA Hardware/General Information/Hardware versioning and tracking - DAVE Developer's Wiki
[18] AURA SOM/AURA Hardware/Peripherals/USB - DAVE Developer's Wiki
[19] AURA SOM/AURA Hardware/Peripherals/I3C - DAVE Developer's Wiki
[20] AURA SOM/AURA Hardware/Peripherals/FlexIO - DAVE Developer's Wiki
[21] AURA SOM/AURA Hardware/Peripherals/Security - DAVE Developer's Wiki
[22] AURA SOM/AURA Hardware/Peripherals/MIPI - DAVE Developer's Wiki
[23] AURA SOM/AURA Hardware/Power and Reset/Reset scheme and control signals - DAVE Developer's Wiki
[24] AURA SOM/AURA Hardware/Peripherals/Ethernet - DAVE Developer's Wiki
[25] AURA SOM/AURA Hardware/Peripherals/I2C - DAVE Developer's Wiki
[26] AURA SOM/AURA Hardware/Peripherals/SPI - DAVE Developer's Wiki
[27] AURA SOM/AURA Hardware/Pinout Table - DAVE Developer's Wiki
[28] AURA SOM/AURA Hardware/Peripherals/ADC - DAVE Developer's Wiki
[29] SOM A vs SOM B comparison table - DAVE Developer's Wiki
[30] Comparison Table - DAVE Developer's Wiki
[31] Thermal management (Axel) - DAVE Developer's Wiki
[32] BORA Lite SOM/BORA Lite Hardware/Electrical Thermal management and heat dissipation - DAVE Developer's Wiki
[33] Thermal tests and measurements (SBCX) - DAVE Developer's Wiki
[34] DESK-MX9-L/pdf - DAVE Developer's Wiki
[35] DESK-MX9-L/General/Release Notes - DAVE Developer's Wiki
[36] BORA Xpress SOM/BORA Xpress Hardware/pdf - DAVE Developer's Wiki
[37] Pinout (BORAXpress) - DAVE Developer's Wiki
[38] BORA Xpress SOM/BORA Xpress Hardware/Pinout Table - DAVE Developer's Wiki
[39] AxelEVB-Lite - DAVE Developer's Wiki
[40] AURA SOM/AURA Evaluation Kit/pdf - DAVE Developer's Wiki
[41] DESK-MX9-L/Deployment/Booting from different storage devices - DAVE Developer's Wiki
[42] BORA SOM/BORA Hardware/Electrical Thermal and Mechanical Features/Operational characteristics - DAVE Developer's Wiki
[43] Power consumption (BoraLite) - DAVE Developer's Wiki
[44] 1200px-AURA_power_lp_bbsm
[45] 1600px-AURA_power_lp_bbsm
[46] DESK-MX9-L/General/DVDK Virtual Machine - DAVE Developer's Wiki
[47] AURA_power_a55_idle_SLD
[48] 20240628151833!AURA_power_a55_stress_OD
[49] 600px-AURA_power_lp_idle
[50] 1600px-AURA-power-sequence
[51] 1600px-AURA_power_lp_suspend
[52] AURA_power_a55_stress_LD
[53] AURA_power_a55_stress_ND
[54] 1600px-AURA_power_lp_idle
[55] AURA SOM/Part number composition - DAVE Developer's Wiki
[56] AURA_power_a55_idle_ND
[57] AURA_power_lp_suspend
[58] 20240621123624!AURA_power_lp_idle
[59] 1599px-AURA_power_a55_stress_OD
[60] BORA SOM/BORA Hardware/Power and Reset/Power Supply Unit (PSU) and recommended power-up sequence - DAVE Developer's Wiki
[61] 1200px-AURA_power_a55_idle_OD
[62] 1200px-AURA_power_m33_wfi_OD
[63] 20240628151742!AURA_power_a55_idle_ND
[64] DESK-MX9-L/Peripherals/Ethernet - DAVE Developer's Wiki
[65] 1200px-AURA_power_lp_idle
[66] 600px-AURA_power_lp_bbsm
[67] 1200px-AURA_power_lp_suspend
[68] 800px-AURA_power_a55_idle_OD
[69] 20240621123603!AURA_power_lp_suspend
[70] Dacu for the Axel SOM - DAVE Developer's Wiki
[71] AURA_power_a55_idle_OD
[72] 20240628152029!AURA_power_lp_idle
[73] 20240212141938!AURA-power-sequence
[74] 800px-AURA_power_lp_idle
[75] BORA SOM/BORA Hardware/Electrical Thermal and Mechanical Features/Mechanical specifications - DAVE Developer's Wiki
[76] BORA SOM/BORA Hardware/Power and Reset/JTAG - DAVE Developer's Wiki
[77] BORA SOM/BORA Hardware/Peripherals/Static memory controller - DAVE Developer's Wiki
[78] BORA SOM/BORA Hardware/Peripherals/UART - DAVE Developer's Wiki
[79] BORA SOM/BORA Hardware/Power and Reset/PL initialization signals - DAVE Developer's Wiki
[80] BORA SOM/BORA Hardware/Peripherals/Real Time Clock - DAVE Developer's Wiki
[81] BORA SOM/BORA Hardware/Peripherals/Processing System (PS) - DAVE Developer's Wiki
[82] BORA SOM/BORA Hardware/Power and Reset/Reset scheme and control signals - DAVE Developer's Wiki
[83] 1600px-AURA_power_a55_idle_ND
[84] BORA SOM/BORA Hardware/Part number composition - DAVE Developer's Wiki
[85] BORA SOM/BORA Hardware/Pinout Table - DAVE Developer's Wiki
[86] BORA SOM/BORA Hardware/Peripherals/Thermal IC - DAVE Developer's Wiki
[87] BORA SOM/BORA Hardware/Peripherals/SDIO - DAVE Developer's Wiki
[88] BORA SOM/BORA Hardware/Peripherals/USB - DAVE Developer's Wiki
[89] BORA SOM/BORA Hardware/Peripherals/Quad-SPI - DAVE Developer's Wiki
[90] BORA SOM/BORA Hardware/Electrical Thermal management and heat dissipation - DAVE Developer's Wiki
[91] BORA SOM/BORA Hardware/Peripherals/Ethernet - DAVE Developer's Wiki
[92] BORA SOM/BORA Hardware/Peripherals/I2C0 - DAVE Developer's Wiki
[93] BORA SOM/BORA Hardware/Peripherals/Watchdog - DAVE Developer's Wiki
[94] BORA SOM/BORA Hardware/Power and Reset/System boot - DAVE Developer's Wiki
[95] BORA SOM/BORA Hardware/Peripherals/EEPROM - DAVE Developer's Wiki
[96] BORA SOM/BORA Hardware/General Information/Hardware versioning and tracking - DAVE Developer's Wiki
[97] BORA SOM/BORA Hardware/pdf - DAVE Developer's Wiki
[98] BORA SOM/BORA Hardware/Peripherals/Programmable logic (FPGA) - DAVE Developer's Wiki
[99] BORA SOM/BORA Hardware/General Information/Processor and memory subsystem - DAVE Developer's Wiki
[100] BORA SOM/BORA Hardware/Peripherals/CAN - DAVE Developer's Wiki
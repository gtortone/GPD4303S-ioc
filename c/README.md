# GPD4303S-ioc
EPICS IOC for GW Instek GPD4303S power supply

## Setup

- edit `configure/RELEASE` and modify `EPICS_BASE`, `ASYN` and `STREAM` to reflect your setup.

## Build

- run `make`

## Configuration

- edit `iocBoot/iocGPD4303Stest/st.cmd` and modify `HOSTNAME` variable with local hostname.

## Run

```
cd iocBoot/iocGPD4303Stest

./st.cmd
```

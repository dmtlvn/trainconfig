# trainconfig
A reproducible manual training pipeline controller. 

### Installation

```shell script
pip install https://github.com/dmtlvn/trainconfig/archive/refs/heads/main.zip
```

### Description

This tool allows to manage train configs (or any other configs) and edit them during runtime from a control panel in 
your browser. All the changes are recorded into a readable YAML file and can be reproduced exactly during consecutive runs. 
This changelog can naturally be added to your git repo and versioned alongside the rest of the project. In other terms,
this package provides tools for manually creating hyper-parameter schedules in real-time.

Config is a nested dictionary (lists are also supported) described in a YAML file with additional syntax. Example:
```yaml
freeze_bn: false
batch_size: 32
chkpt_dir: "./checkpoints"
generator:
  image_size: 256
  latent_size: 512
  opt:
    lr: 1e-4
    betas:
    - 0.5
    - 0.999   
```  
The corresponding changelog may look something like this:
```yaml
0:
  freeze_bn: false
  batch_size: 32
  chkpt_dir: "./checkpoints"
  generator:
    image_size: 256
    latent_size: 512
    opt:
      lr: 1e-4
      betas:
      - 0.5
      - 0.999  
69:
  generator:
    opt:
      lr: 2e-4
420:
  batch_size: 16
```
The changes are logged by the step number, and the 0's record is always a full config. This allows to reconstruct the 
the state of the config at every training step. 

Additional modifiers can be added to dictionary keys. They define how the corresponding field will appear on the control
panel. The general pattern is `key_name[dtype|param|param|...]!`. This feature is only partially supported at the moment:
- By default a value is represented as a text field in the control panel.
- If the key ends with `!`, its corresponding field will be disabled to prevent unintended edits. This is useful for 
static parameters, like number of GPUs used, for example, and for cleaner changelogs.
- Boolean values are automatically displayed as checkboxes.

*A planned support also includes **optional** data type descriptions for smarter controls selection. 
Currently, info in brackets is ignored.*

Control panel is a streamlit app which displays the editing form according to the provided YAML file. It allows 
editing config values in realtime and sends these updates to a config manager. 

Config manager is a `Config` object, which keeps track of all the changes made via the control panel and always 
provides up-to-date values. This is the main interface your code should interact with. It is implemented as a static 
class and shares its data across all modules (but not across processes). For convenience, all the values 
in the `Config` object can be accessed in an attribute-like fashion.

Config manager provides a `editable` toggle, which allows edits from the control panel. Unset it if you make a scheduled 
run to prevent unwanted edits.

**IMPORTANT:** If `editable` toggle is set, and changes are made to the config via the control panel mid-schedule, 
**the rest of the schedule from the current step will be overwritten!**. This feature was left for easier experimentation
purposes, but should be used with caution, because may lead to the loss of the changelog information.

### Usage

1. Start your main training script. Here's an example of dynamically updating a learning rate during training. The `init()` 
method accepts a path to a base config file, path to a changelog file, `initial_step` number and a `editable` flag. 
Setting the initial step fast-forwards all the changes to a given step. At the beginning of each iteration update the 
config. This will pull fresh parameter values from the changelog file or from the web form. Call `Config.close()` at the
end of the script to perform cleanup.
```python
from trainconfig import Config as C

C.init('config.yaml', 'changelog.yaml', initial_step = 10000, editable = True)
 ... 
for batch in data_loader:
    C.update()
    ...
    for params in optimizer.param_groups:
            params['lr'] = C.generator.opt.lr
    ...    
...
C.close()
```
Each `Config.update()` call increments the step number.

2. In your terminal start the control panel and follow the provided URL:
```
trainconfig [PORT]  # by default it runs on a 8501 port
```

### Known Issues

- Different sessions are not supported at the moment, so don't run multiple train scripts on the same machine at once
- The control panel relies on a built-in streamlit mechanism which updates the page on every change, so only a single 
value can be edited at a time, but this mechanism isn't well documented so there can be some corner cases.


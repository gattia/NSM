import torch 
import os
import math

class LearningRateSchedule:
    def get_learning_rate(self, epoch):
        pass


class ConstantLearningRateSchedule(LearningRateSchedule):
    def __init__(self, value):
        self.value = value

    def get_learning_rate(self, epoch):
        return self.value


class StepLearningRateSchedule(LearningRateSchedule):
    def __init__(self, initial, interval, factor):
        self.initial = initial
        self.interval = interval
        self.factor = factor

    def get_learning_rate(self, epoch):

        return self.initial * (self.factor ** (epoch // self.interval))


class WarmupLearningRateSchedule(LearningRateSchedule):
    def __init__(self, initial, warmed_up, length):
        self.initial = initial
        self.warmed_up = warmed_up
        self.length = length

    def get_learning_rate(self, epoch):
        if epoch > self.length:
            return self.warmed_up
        return self.initial + (self.warmed_up - self.initial) * epoch / self.length


def get_learning_rate_schedules(config):

    schedule_specs = config["LearningRateSchedule"]

    schedules = []

    for schedule_specs in schedule_specs:

        if schedule_specs["Type"] == "Step":
            schedules.append(
                StepLearningRateSchedule(
                    schedule_specs["Initial"],
                    schedule_specs["Interval"],
                    schedule_specs["Factor"],
                )
            )
        elif schedule_specs["Type"] == "Warmup":
            schedules.append(
                WarmupLearningRateSchedule(
                    schedule_specs["Initial"],
                    schedule_specs["Final"],
                    schedule_specs["Length"],
                )
            )
        elif schedule_specs["Type"] == "Constant":
            schedules.append(ConstantLearningRateSchedule(schedule_specs["Value"]))

        else:
            raise Exception(
                'no known learning rate schedule of type "{}"'.format(
                    schedule_specs["Type"]
                )
            )

    return schedules

def adjust_learning_rate(lr_schedules, optimizer, epoch, verbose=False):
    if verbose is True:
        print("optimizer param groups: ", optimizer.param_groups)
        print('lr_schedules: ', lr_schedules)
    for i, param_group in enumerate(optimizer.param_groups):
        param_group["lr"] = lr_schedules[i].get_learning_rate(epoch)

# def save_checkpoints(epoch, config, model, epoch):
#         save_model(config['experiment_directory'], str(epoch) + ".pth", decoder, epoch)
#         save_optimizer(experiment_directory, str(epoch) + ".pth", optimizer_all, epoch)
#         save_latent_vectors(experiment_directory, str(epoch) + ".pth", lat_vecs, epoch)

def save_latent_vectors(config, epoch, latent_vec, latent_codes_subdir="latent_codes"):
    filename = f'{epoch}.pth'
    folder_save = os.path.join(config['experiment_directory'], latent_codes_subdir)
    if not os.path.exists(folder_save):
        os.makedirs(folder_save, exist_ok=True)

    all_latents = latent_vec.state_dict()

    torch.save(
        {"epoch": epoch, "latent_codes": all_latents},
        os.path.join(folder_save, filename),
    )

def save_model(config, epoch, decoder, model_subdir="model"):
    if type(decoder) not in (list, tuple):
        decoder = [decoder]
    
    filename = f'{epoch}.pth'
    
    for decoder_idx, decoder_ in enumerate(decoder):
        if len(decoder) > 1:
            model_subdir_ = model_subdir + f'_{decoder_idx}'
        else:
            model_subdir_ = model_subdir
            
        folder_save = os.path.join(config['experiment_directory'], model_subdir_)
        if not os.path.exists(folder_save):
            os.makedirs(folder_save, exist_ok=True)
        
        torch.save(
            {"epoch": epoch, "model": decoder_.state_dict()},
            os.path.join(folder_save, filename),
        )

def get_checkpoints(config):
    checkpoints = list(
        range(
            config['checkpoint_epochs'],
            config['n_epochs'] + 1,
            config['checkpoint_epochs'],
        )
    )

    for checkpoint in config['additional_checkpoints']:
        checkpoints.append(checkpoint)
    checkpoints.sort()

    return checkpoints

def get_latent_vecs(num_objects, config):
    lat_vecs = torch.nn.Embedding(num_objects, config['latent_size'], max_norm=config['latent_bound'])
    torch.nn.init.normal_(
        lat_vecs.weight.data,
        0.0,
        config['latent_init_std'] / math.sqrt(config['latent_size']),
    )

    return lat_vecs

def get_optimizer(model, latent_vecs, lr_schedules, optimizer="Adam", weight_decay=0.0001):
    if type(model) not in (list, tuple):
        model = [model]
    
    list_params = [
        {
            "params": latent_vecs.parameters(),
            "lr": lr_schedules[1].get_learning_rate(0),
        }
    ]
    for model_ in model:
        list_params.append(
            {
                "params": model_.parameters(),
                "lr": lr_schedules[0].get_learning_rate(0),
            }
        )

    if optimizer == "Adam":
        optimizer = torch.optim.Adam(list_params)
    elif optimizer == "AdamW":
        optimizer = torch.optim.AdamW(list_params, weight_decay=weight_decay)

    return optimizer


def symmetric_chammfer(p1, p2, n_pts):
    """
    """
    pass
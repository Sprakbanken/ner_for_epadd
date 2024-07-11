from torch.utils.data import Dataset


class DictDataset(Dataset):
    def __init__(self, data: dict):
        self.keys = []
        self.values = []
        for k,v in data.items():
            self.keys.append(k)
            self.values.append(v)

    def __len__(self):
        return len(self.keys)

    def __getitem__(self, i):
        return self.values[i]

from torch.utils.data import Dataset


class EmailDataset(Dataset):
    def __init__(self, data: dict):
        self.message_ids = []
        self.message_texts = []
        for k, v in data.items():
            self.message_ids.append(k)
            self.message_texts.append(v)

    def __len__(self):
        return len(self.message_ids)

    def __getitem__(self, i):
        return self.message_texts[i]

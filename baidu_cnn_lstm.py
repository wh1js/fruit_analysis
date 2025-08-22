import numpy as np
import paddle
import paddle.nn as nn
import json


def normalize_input(input_data, mean, std):
    return (input_data - mean) / std


def denormalize_output(output_data, mean, std):
    return output_data * std + mean


class CNNLSTMModel(nn.Layer):
    def __init__(self, dropout_rate=0.3):
        super(CNNLSTMModel, self).__init__()
        # CNN with simplified structure for partial compatibility
        self.cnn = nn.Sequential(
            nn.Conv1D(in_channels=1, out_channels=64, kernel_size=5, stride=1, padding=2),
            nn.BatchNorm1D(64),
            nn.ReLU(),
            nn.Conv1D(in_channels=64, out_channels=128, kernel_size=5, stride=1, padding=2),
            nn.BatchNorm1D(128),
            nn.ReLU(),
            nn.Dropout(dropout_rate)
        )
        # Residual connection adapter
        self.residual_adapter = nn.Conv1D(in_channels=1, out_channels=128, kernel_size=1, stride=1)

        # Bidirectional LSTM with reduced layers for efficiency
        self.lstm = nn.LSTM(input_size=128, hidden_size=128, num_layers=1, direction='bidirectional', dropout=0.0)

        # Fully connected layers
        self.fc = nn.Sequential(
            nn.Linear(128 * 2, 512),  # *2 for bidirectional LSTM
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(512, 3)
        )

    def forward(self, x):
        # Input shape: [batch_size, 12]
        x = x.unsqueeze(1)  # [batch_size, 1, 12]

        # Residual connection
        residual = self.residual_adapter(x)  # [batch_size, 128, 12]

        # CNN
        x = self.cnn(x)  # [batch_size, 128, 12]

        # Add residual connection
        x = x + residual  # [batch_size, 128, 12]
        x = nn.functional.relu(x)

        # Prepare for LSTM
        x = x.transpose([0, 2, 1])  # [batch_size, 12, 128]

        # LSTM
        out, _ = self.lstm(x)  # [batch_size, 12, 256] (bidirectional: 128 * 2)

        # Use the last time step
        out = out[:, -1, :]  # [batch_size, 256]

        # Fully connected
        out = self.fc(out)  # [batch_size, 3]
        return out


def baidu_cnnlstm(spectrum_file_path):
    # Load normalization parameters
    measure_mean = np.load('baidu-cnn-lstm/weights/measure_mean.npy')
    measure_std = np.load('baidu-cnn-lstm/weights/measure_std.npy')
    label_mean = np.load('baidu-cnn-lstm/weights/label_mean.npy')
    label_std = np.load('baidu-cnn-lstm/weights/label_std.npy')

    # Set device
    device = paddle.set_device('cpu')

    # Load model
    model = CNNLSTMModel()

    # Load weights manually to handle partial compatibility
    pretrained_dict = paddle.load('baidu-cnn-lstm/weights/model.pdparams')
    model_dict = model.state_dict()

    # Filter compatible weights
    compatible_dict = {k: v for k, v in pretrained_dict.items() if k in model_dict and v.shape == model_dict[k].shape}
    
    # Update model with compatible weights
    model_dict.update(compatible_dict)
    model.set_state_dict(model_dict)
    model.eval()

    # Extract spectrum data
    keys_order = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8',
                  'Clear1', 'NIR1', 'Clear2', 'NIR2']

    rows = []
    with open(spectrum_file_path, 'r') as f:
        for line in f:
            data = json.loads(line.strip())
            inner_dict = list(data.values())[0]
            row = [inner_dict[key] for key in keys_order]
            rows.append(row)

    # Calculate column averages
    averages = [sum(col) / len(rows) for col in zip(*rows)]
    numbers = [float(f"{avg:.2f}") for avg in averages]

    # Prediction
    new_input = np.array(numbers)
    normalized_input = normalize_input(new_input, measure_mean, measure_std)
    input_tensor = paddle.to_tensor(normalized_input, dtype='float32').unsqueeze(0)

    with paddle.no_grad():
        prediction = model(input_tensor)
        prediction = prediction.numpy()[0]
        real_prediction = denormalize_output(prediction, label_mean, label_std)

    # Extract predicted values
    ph, water, sugar = real_prediction.tolist()
    return ph, water, sugar


if __name__ == "__main__":
    txt = "upload_images/1754984861/specturm.txt"
    ph, water, sugar = baidu_cnnlstm(txt)
    print('ph: {}\nwater: {}\nsugar: {}'.format(ph, water, sugar))
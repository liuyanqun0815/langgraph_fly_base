import os
import wave
from scipy.io.wavfile import write as write_wav
from IPython.display import Audio
import ChatTTS
from omegaconf import OmegaConf
import numpy as np

SAMPLE_RATE = 24000
download_path ="E:\model\pzc163\chatTTS"
chat = ChatTTS.Chat()

chat.load_models(device='cpu',**{k: os.path.join(download_path, v) for k, v in
              OmegaConf.load(os.path.join(download_path, 'config', 'path.yaml')).items()})

texts = ["如果你的模型使用的是不同的格式或需要不同的库来保存语音，你需要根据模型的文档和输出格式来调整保存文件的代码。如果你需要进一步的帮助，请提供更多的上下文信息，例如模型的具体实现细节和输出数据的格式",]

wavs = chat.infer(texts, use_decoder=True)
rate = 24_000

# 将NumPy数组转换为字节数据
# 如果wavs[0]已经是16位PCM格式，直接转换为字节流
# 如果wavs[0]是浮点数数组，需要先标准化到[-1, 1]区间，然后转换到16位PCM
if wavs[0].dtype == np.float32 or wavs[0].dtype == np.float64:
    # 标准化音频数据到[-1, 1]区间
    wavs[0] = wavs[0] / np.max(np.abs(wavs[0]))
    # 转换到16位PCM格式
    wavs[0] = (wavs[0] * 32767).astype(np.int16)

# 定义文件名和路径
filename = "output.wav"
filepath = os.path.join(download_path, filename)

# 打开一个WAV文件进行写入
with wave.open(filepath, 'wb') as wf:
    # 设置参数，这里假设是单声道，采样率为24000Hz，样本宽度为2字节（16位）
    wf.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))

    # 将音频数据写入文件
    wf.writeframes(wavs[0].tobytes())

print(f"音频已保存到 {filepath}")
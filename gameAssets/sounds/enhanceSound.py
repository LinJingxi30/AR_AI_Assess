from pydub import AudioSegment

def amplify_wav(input_file, output_file, gain_dB):
    """
    放大 WAV 文件的声音并输出到新的文件。
    
    参数:
    - input_file: 输入的 WAV 文件路径
    - output_file: 输出的 WAV 文件路径
    - gain_dB: 增益值（以分贝为单位，正值表示放大，负值表示减小）
    """
    try:
        # 加载音频文件
        audio = AudioSegment.from_file(input_file, format="wav")
        
        # 增加音量
        amplified_audio = audio + gain_dB
        
        # 导出放大后的音频
        amplified_audio.export(output_file, format="wav")
        print(f"放大后的音频已保存到: {output_file}")
    except Exception as e:
        print(f"处理音频时出错: {e}")

if __name__ == "__main__":
    # 输入文件路径
    input_wav = "perfect.wav"  # 替换为你的输入文件路径
    # 输出文件路径
    output_wav = "perfect2.wav"  # 替换为你的输出文件路径
    # 增益值（分贝）
    gain = 30  # 增加 10 分贝
    
    amplify_wav(input_wav, output_wav, gain)
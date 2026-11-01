"""Exact official Eglantine executables reviewed for the container probe.

Build 96: e96917cd0e68851ec389dd519f03b52adc11d493.
https://github.com/Djihads80/Eglantine/releases/tag/build-96
Unknown builds must never be guessed from a filename or version string.
"""
PROFILES = {
    '245e350c32af4d91f852b11d9b301ee2f57ff74cf98cbcd0fc25853627a0a106':
        {'name':'PokeDinner 2.0.0 · 70ecb39ef0 · Windows x64', 'file':'eglantine.exe', 'abi':'msvc-read9',
         'hook':0x2fe638,'expected':'4c8d7dc04c89f9','kind':'inline-pokedinner'},
    'e3ec0b859e6e1ff2dec03865a3c8a11b547ad84521898091e21ab1c40d3927ec':
        {'name':'PokeDinner 2.0.0 · 70ecb39ef0 · Windows x64 CLI', 'file':'eden-cli.exe', 'abi':'msvc-read9',
         'hook':0x79458,'expected':'4c8d7dc04c89f9','kind':'inline-pokedinner'},
    '1528c11cff882d5b8b7d0dda83b57925700201b55f13471c8b62c79ea1275db8':
        {'name':'Eglantine build 96 · Windows x64', 'file':'eglantine.exe', 'abi':'msvc',
         'hook':0x459c40,'expected':'48895c2410','kind':'entry'},
    'cb89d931b603f604afe552ace6bbdde1a4dbbcf6431919b04c739043e30d19d4':
        {'name':'Eglantine build 96 · Windows x64 CLI', 'file':'eden-cli.exe', 'abi':'msvc',
         'hook':0x293020,'expected':'48895c2410','kind':'entry'},
    'a5e408544daa7a20d9506024410a468cb235cdedcfb9a6a7a8c9c2bcce43a8a0':
        {'name':'Eglantine build 96 · Windows x64 PGO', 'file':'eglantine.exe', 'abi':'gnu',
         'hook':0x1f6ea,'expected':'488d8c2480010000','kind':'inline'},
    '37f8ad2a67e6b6faf6f1d513d1adac12c5bfb144cf6bb53807bda008f059c7e7':
        {'name':'Eglantine build 96 · Windows x64 PGO CLI', 'file':'eden-cli.exe', 'abi':'gnu',
         'hook':0x1f92a,'expected':'488d8c2480010000','kind':'inline'},
}

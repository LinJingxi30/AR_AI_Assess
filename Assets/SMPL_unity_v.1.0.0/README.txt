License:
--------
Copyright 2017 Naureen Mahmood, Matthew Loper and the Max Planck Gesellschaft. All rights reserved. This software is provided for research purposes only.
By using this software you agree to the terms of the SMPL Model license here http://smpl.is.tue.mpg.de/license

Special thanks to Joachim Tesch and Max Planck Institute for Biological Cybernetics in helping create and test these scripts for Unity.

To get more information about SMPL and other downloads visit: http://smpl.is.tue.mpg.
For comments or questions, please email us at: smpl@tuebingen.mpg.de


Please Note:
-----------
This is a demo version of the scripts & sample project for using the SMPL model's shape-blendshapes & corrective pose-blendshapes inside Unity. We would be happy to receive comments, help and suggestions on improving the model and in making it available on more platforms. 


System Requirements
-------------------
The Unity scripts have been tested in Unity 5+ on Windows 7+10 and MacOS Sierra

Minimum requirement for the SMPL_Mecanim project: 
- Unity 5.6.0f3
- OS: Windows/Mac/Linux


About the Downloads:
--------------------------
The Unity Download includes the male & female SMPL model FBX files & scripts to support using SMPL in Unity. This download is a zipped archive called ‘SMPL_unity_v.1.0.0.zip' which contains the following files and folders:

•   SMPL directory:
    o   Models directory
        •   Male & Female SMPL models as Unity-compatible FBX files
            •   ../SMPL/Models/SMPL_f_unityDoubleBlends_lbs_10_scale5_207_v1.0.0.fbx
            •   ../SMPL/Models/SMPL_m_unityDoubleBlends_lbs_10_scale5_207_v1.0.0.fbx
    o   Samples directory
        •   Male & Female sample texture-maps
            •   ../SMPL/Samples/Materials/SMPL_sampleTex_f.jpg
            •   ../SMPL/Samples/Materials/SMPL_sampleTex_m.jpg
        •   Male & Female sample shape-parameters as JSON files
            •   ../SMPL/Samples/Betas/SMPL_sampleShape1_f.json
            •   ../SMPL/Samples/Betas/SMPL_sampleShape2_f.json
            •   ../SMPL/Samples/Betas/SMPL_sampleShape1_m.json
            •   ../SMPL/Samples/Betas/SMPL_sampleShape2_m.json
    o   Scripts directory
        •   Male & Female joint-regressors as JSON files
            •   ../SMPL/Scripts/MPI/jnt_regressors/SMPL_jReg_f_lbs_v1.0.0.json
            •   ../SMPL/Scripts/MPI/jnt_regressors/SMPL_jReg_m_lbs_v1.0.0.json
        •   C# scripts for using SMPL model in Unity
            •   ../SMPL/Scripts/MPI/SMPLBlendshapes.cs
            •   ../SMPL/Scripts/MPI/SMPLJointCalculator.cs 
            •   ../SMPL/Scripts/MPI/SMPLModifyBones.cs
            •   ../SMPL/Scripts/MPI/SMPLOptimalPoseBlends.cs
        •   Third party C# scripts for reading JSON files & matrix manipulation (including relevant licenses):
            •   ../SMPL/Scripts/ThirdParty/Matrix
            •   ../SMPL/Scripts/ThirdParty/JSON
•   SMPL_mecanim directory containing a sample Unity project
•   README.txt file containing installation instructions
•   How-to_SMPLinUnity.pdf file containing a step-by-step guide to setup and use SMPL model in Unity



Using the C# Scripts:
--------------------
The C# scripts provided here can be used to load and animate SMPL caharacters in your own project. A step-by-step guide on how to set up the SMPL model inside Unity for your own project is provided in the How-to_SMPLinUnity.pdf file.


About the Sample Project:
------------------------
The sample project is provided to help you get started with SMPL in Unity. The project already contains the SMPL models and sample files. The sample project can be run as is and it shows the ability to use the SMPL male & female characters in a game engine and move them around using keypad controllers. For detailed instructions on how to run the project on your own machine, please consult the included How-to PDF file.


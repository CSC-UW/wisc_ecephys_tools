addpath(genpath('/Volumes/scratch/neuropixels/matlab/external/Kilosort-tb-v2.5'));

F_orig = readNPY('F_orig.npy');
F0_orig = readNPY('F0_orig.npy');
F_orig = readNPY('F_long.npy');
ysamp = linspace(1.5, 7631.5, size(F,1))
nblocks = 5;
nblocks = 10;
nblocks=5

[imin, yblk, F0, F0m, F_aligned] = align_block2(F_orig, ysamp, nblocks);

writeNPY(gather(F_orig), fullfile('F_input.npy'));
writeNPY(gather(F0), fullfile('F0_comp_orig.npy'));
writeNPY(gather(F0m), fullfile('F0m_comp_orig.npy'));
writeNPY(gather(F_aligned), fullfile('F_comp_aligned.npy'));
writeNPY(imin, 'imin_comp_orig.npy')

[imin_test, yblk, F0_test, F0m_test, F_test_aligned] = align_block2_nonrigid_target(F_orig, ysamp, nblocks);

writeNPY(gather(F0_test), fullfile('F0_test.npy'));
writeNPY(gather(F0m_test), fullfile('F0m_test.npy'));
writeNPY(gather(F_test_aligned), fullfile('F_test_aligned.npy'));
writeNPY(imin_test, 'imin_test.npy')


F_sim = readNPY('F_sim.npy');

[imin_sim, yblk, F0_sim, F0m_sim] = align_block2_nonrigid_target(F_sim, ysamp, nblocks)
[imin_sim, yblk, F0_sim, F0m_sim] = align_block2(F_sim, ysamp, nblocks)

writeNPY(gather(F0_sim), fullfile('F0_sim.npy'));
writeNPY(gather(F0m_sim), fullfile('F0m_sim.npy'));
writeNPY(imin_sim, 'imin_sim.npy')
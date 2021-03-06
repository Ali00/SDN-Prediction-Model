 ### Network prediction framework:
The framework has been evaluated by the SDN emulator "Mininet": http://mininet.org/ with POX as a network operating system
(controller): https://github.com/noxrepo/pox/ 
<div class="container">
  <div class="subcontainer">
    <figure>
      <p align="center">
      <img  src="https://user-images.githubusercontent.com/12594727/50406378-1ccdb480-07bc-11e9-8646-0676a22d4cee.png" width="300" height="300"/>
      <figcaption><p align="center">Fig.1:Framework architecture</figcaption>
    </figure>
  </div>
</div>

### Network topology: 
The network is modelled as an undirected graph G(V,E), hence, we utilised the NetworkX tool, https://networkx.github.io/, (version 1.11). Waxman.brite topology has been created via BRITE tool: https://www.cs.bu.edu/brite/ and parsed by the FNSS simulator: https://fnss.github.io/ to represent the data plane topology.

  <div class="container">
  <div class="subcontainer">
    <figure>
      <p align="center">
      <img  src="https://user-images.githubusercontent.com/12594727/49808997-b7a6a780-fd55-11e8-8645-dc3cc944acd7.png" width="200" height="200"/>
      <figcaption><p align="center">Fig.2:Waxman Topology layout</figcaption>
    </figure>
  </div>
</div>

### Network prediction model:
<div class="container">
  <div class="subcontainer">
    <figure>
      <p align="center">
      <img  src="https://user-images.githubusercontent.com/12594727/50402914-4a9e0380-0792-11e9-9a9e-e59842e7245f.png" width="600" height="120"/>
      <figcaption><p align="center"> Fig.3:Online failure prediction </figcaption>
    </figure>
  </div>
</div>

![#f03c15](https://placehold.it/15/f03c15/000000?text=+) `If you use this framework or any of its code in your work then, please cite the following publication: "Smart routing: Towards proactive fault handling of software-defined
networks",`<br>
`@article{malik2020smart,`<br>
  `title={Smart routing: towards proactive fault handling of software-defined networks},`<br>
  `author={Malik, Ali and Aziz, Benjamin and Adda, Mo and Ke, Chih-Heng},`<br>
  `journal={Computer Networks},`<br>
  `pages={107104},`<br>
  `year={2020},`<br>
  `publisher={Elsevier}`
`}`
<br> https://www.sciencedirect.com/science/article/abs/pii/S1389128619300271#!



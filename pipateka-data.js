const BBDD_TABACOS = [
  {
    id:'peterson-nightcap', nombre:'Nightcap', marca:'Peterson', tipo:'Inglés / Latakia', corte:'Ribbon', fuerza:5, aroma:'Humo, madera, especias y notas profundas de Latakia; sala intensa.', composicion:'Virginia, Latakia, Oriental/Turco y Perique.', valoracion:3.46, popularidad:100, disponibilidad:'Disponible actualmente en Europa; la presentación y disponibilidad pueden variar por país.', imagen:'assets/tins/editorial-tin.svg',
    reseñas:[
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'La conversación comunitaria lo sitúa como una mezcla nocturna potente, ahumada y compleja. Se repiten las referencias a Latakia marcada, especias y una sensación de cuerpo completo; también aparece con frecuencia la advertencia de que su fortaleza no es para todos.'},
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'Las opiniones más favorables destacan la evolución del humo y la combinación de Virginia, Orientales y Perique. Las menos favorables suelen concentrarse en la fuerza y en una sala que puede resultar muy intensa.'}
    ]
  },
  {
    id:'peterson-early-morning-pipe', nombre:'Early Morning Pipe', marca:'Peterson', tipo:'Inglés ligero / Oriental', corte:'Ribbon', fuerza:2, aroma:'Heno dulce, especias suaves, humo delicado y fondo ligeramente terroso.', composicion:'Virginia, Oriental/Turco y Latakia en proporción ligera.', valoracion:3.55, popularidad:96, disponibilidad:'Disponible actualmente en Europa; disponibilidad dependiente del mercado.', imagen:'assets/tins/editorial-tin.svg',
    reseñas:[
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'La comunidad suele describirlo como una puerta de entrada amable a las mezclas inglesas: ligero, aromático de forma natural y especialmente apropiado para las primeras horas del día.'},
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'Se repiten notas de heno, pan tostado y especias orientales. Algunos fumadores señalan que puede mostrar amargor al final si se fuma demasiado caliente o en una pipa grande.'}
    ]
  },
  {
    id:'samuel-gawith-1792-flake', nombre:'1792 Flake', marca:'Samuel Gawith', tipo:'Virginia / Aromatizado', corte:'Flake', fuerza:5, aroma:'Oscuro, terroso y profundo, con carácter distintivo de tonquin.', composicion:'Virginia curado a presión con aromatización característica de tonquin.', valoracion:3.39, popularidad:88, disponibilidad:'Disponible de forma intermitente en Europa según país y existencias.', imagen:'assets/tins/editorial-tin.svg',
    reseñas:[
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'Las opiniones lo presentan como un flake de personalidad extrema: Virginia oscuro, humo denso y una nota aromática muy reconocible. Divide a los fumadores entre admiradores y detractores.'},
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:3, texto:'Quienes lo disfrutan destacan su profundidad y carácter tradicional; quienes no conectan con él suelen señalar la intensidad del tonquin y una fortaleza elevada.'}
    ]
  },
  {
    id:'ashton-winding-road', nombre:'Winding Road', marca:'Ashton', tipo:'Inglés / Latakia', corte:'Ribbon', fuerza:3, aroma:'Humo dulce, madera, tierra y especias orientales.', composicion:'Virginia, Latakia, Orientales y Burley.', valoracion:3.62, popularidad:84, disponibilidad:'Disponibilidad europea variable; consultar el mercado local.', imagen:'assets/tins/editorial-tin.svg',
    reseñas:[
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'La recepción suele valorar su equilibrio entre humo y dulzor natural. Se percibe como una mezcla inglesa de intensidad media, menos agresiva que los grandes latakiados nocturnos.'},
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'Los comentarios favorables hablan de una combustión cómoda y de un perfil que gana interés conforme avanza la cazoleta, con tierra, madera y especias.'}
    ]
  },
  {
    id:'rattrays-black-mallory', nombre:'Black Mallory', marca:"Rattray's", tipo:'Inglés / Latakia', corte:'Ribbon', fuerza:4, aroma:'Humo oscuro, cuero, madera y especias; sala marcada.', composicion:'Latakia, Virginia, Burley y Orientales.', valoracion:3.63, popularidad:82, disponibilidad:'Disponible en determinados mercados europeos; stock variable.', imagen:'assets/tins/editorial-tin.svg',
    reseñas:[
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'La comunidad suele situarlo en la zona media-alta de intensidad, con Latakia perceptible pero acompañada por dulzor de Virginia y una base terrosa.'},
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'Se aprecia especialmente por su carácter clásico y por la evolución de especias, cuero y madera durante la fumada. Para algunos paladares puede resultar demasiado oscuro.'}
    ]
  },
  {
    id:'mac-baren-navy-flake', nombre:'Navy Flake', marca:'Mac Baren', tipo:'Virginia / Burley / Aromático', corte:'Flake', fuerza:3, aroma:'Dulce, afrutado, floral y ligeramente especiado; sala agradable.', composicion:'Virginia, Burley y Cavendish.', valoracion:3.10, popularidad:91, disponibilidad:'Amplia disponibilidad europea, aunque puede variar por país.', imagen:'assets/tins/mac-baren--navy-flake.jpg',
    reseñas:[
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'Las reseñas suelen coincidir en una entrada dulce y afrutada, con una base de Burley más terrosa y ligeramente nuez conforme avanza la fumada.'},
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:3, texto:'Se valora por su facilidad de uso y por una sala amable. Las críticas más habituales apuntan a un dulzor que puede dominar si se fuma buscando un perfil puramente natural.'}
    ]
  },
  {
    id:'mac-baren-plumcake', nombre:'Plumcake', marca:'Mac Baren', tipo:'Virginia / Latakia / Aromático', corte:'Flake', fuerza:3, aroma:'Fruta madura, especias, madera y humo suave.', composicion:'Virginia, Burley, Latakia y Cavendish.', valoracion:3.50, popularidad:86, disponibilidad:'Disponible en varios mercados europeos; existencias variables.', imagen:'assets/tins/mac-baren--plumcake.jpg',
    reseñas:[
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'La percepción general combina fruta oscura y especias con un fondo ahumado. Suele recomendarse a quien quiere pasar de aromáticos a mezclas con más profundidad.'},
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'Los comentarios positivos destacan su complejidad y evolución; otros consideran que el componente aromático puede variar bastante según la velocidad de fumada.'}
    ]
  },
  {
    id:'mac-baren-dark-twist', nombre:'Dark Twist', marca:'Mac Baren', tipo:'Virginia / Burley', corte:'Roll Cake', fuerza:3, aroma:'Pan tostado, frutos secos, cacao ligero y dulzor natural.', composicion:'Virginia y Burley en discos enrollados.', valoracion:3.46, popularidad:87, disponibilidad:'Disponible en Europa en varios mercados especializados.', imagen:'assets/tins/mac-baren--dark-twist.jpg',
    reseñas:[
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'La comunidad suele apreciar la presentación en roll cake y un sabor progresivo que mezcla dulzor de Virginia con el carácter tostado del Burley.'},
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'Se describe como versátil y de fortaleza media. Las opiniones menos favorables suelen pedir más intensidad o una evolución más dramática.'}
    ]
  },
  {
    id:'mac-baren-club-blend', nombre:'Club Blend', marca:'Mac Baren', tipo:'Aromático / Virginia / Burley', corte:'Ribbon', fuerza:2, aroma:'Frutos secos, vainilla suave, azúcar tostado y tabaco dulce.', composicion:'Virginia, Burley y Cavendish.', valoracion:3.20, popularidad:79, disponibilidad:'Disponible en diversos mercados europeos.', imagen:'assets/tins/mac-baren--club-blend.jpg',
    reseñas:[
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'Las opiniones suelen presentarlo como un aromático clásico, suave y fácil de abordar, con un equilibrio razonable entre topping y sabor de hoja.'},
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:3, texto:'Los fumadores que buscan naturalidad pueden encontrarlo demasiado dulce, mientras que quienes prefieren aromáticos valoran especialmente su sala.'}
    ]
  },
  {
    id:'peterson-university-flake', nombre:'University Flake', marca:'Peterson', tipo:'Virginia / Perique / Burley', corte:'Flake', fuerza:4, aroma:'Pan, fruta seca, especias y tabaco curado.', composicion:'Virginia, Perique y Burley.', valoracion:3.74, popularidad:90, disponibilidad:'Disponible actualmente en Europa; disponibilidad variable.', imagen:'assets/tins/editorial-tin.svg',
    reseñas:[
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'La comunidad destaca su cuerpo medio-alto, dulzor de Virginia y el toque especiado del Perique. Se menciona a menudo como un flake serio para fumadas pausadas.'},
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'Los comentarios también señalan que necesita algo de atención al encendido y al prensado, pero recompensa con una fumada larga y estable.'}
    ]
  },
  {
    id:'samuel-gawith-full-virginia-flake', nombre:'Full Virginia Flake', marca:'Samuel Gawith', tipo:'Virginia', corte:'Flake', fuerza:3, aroma:'Heno, pan, fruta madura, melaza y dulzor de hoja.', composicion:'Virginia prensado y curado en flake.', valoracion:3.76, popularidad:95, disponibilidad:'Disponible en Europa con existencias variables según mercado.', imagen:'assets/tins/editorial-tin.svg',
    reseñas:[
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'La conversación comunitaria lo considera un referente del Virginia prensado: dulce, profundo y capaz de mostrar notas de pan, fruta y heno.'},
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'La crítica recurrente se centra en la humedad y el encendido cuando se abre fresco; bien preparado, suele recibir elogios por su profundidad.'}
    ]
  },
  {
    id:'samuel-gawith-hh-latakia-flake', nombre:'HH Latakia Flake', marca:'Mac Baren / HH', tipo:'Inglés / Latakia', corte:'Flake', fuerza:4, aroma:'Humo, cuero, turba, especias y madera oscura.', composicion:'Virginia, Latakia y Orientales.', valoracion:3.68, popularidad:83, disponibilidad:'Disponible en mercados europeos especializados.', imagen:'assets/tins/mac-baren--hh-latakia-flake.jpg',
    reseñas:[
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'Los aficionados valoran el carácter ahumado y la estructura de flake, con una Latakia clara pero integrada en una base dulce y especiada.'},
      {usuario:'Síntesis de comunidad', fecha:'2026-09-15', puntuacion:4, texto:'Se suele recomendar a fumadores con experiencia en mezclas inglesas. La sala es intensa y el ritmo lento favorece una mejor definición de las hojas.'}
    ]
  }
];

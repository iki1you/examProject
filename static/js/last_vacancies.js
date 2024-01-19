fetch("https://api.hh.ru/vacancies?search_field=name&text=':(инженер AND программист)'&order_by=publication_time&per_page=10&only_with_salary=True")
  .then((response) => response.json())
  .then(async (answer) => {
      const data = [];
      const vacancies = answer['items'];
      for (const element of vacancies) {
          const response = await fetch('https://api.hh.ru/vacancies/' + element['id'] )
          const answer = await response.json()
          data.push([answer['name'], answer['employer']['name'], answer['salary'], answer['area']['name'], answer['published_at'], answer['description'], answer['key_skills']]);
      }
      return data;
  }).then((answer) => renderVacancies(answer)).catch((err) => { alert(err.message) } );

const renderVacancies = (data) => {
    const picturesList = document.querySelector('.vacancies');
    const pictureTemplate = document.querySelector('#element-template').content;
    const pictureListFragment = document.createDocumentFragment();
    console.log(data);
    data.forEach((element) => {
       const newPicture = pictureTemplate.cloneNode(true);
       newPicture.querySelector('span').textContent = element[0] + ' ' + element[1] + ' ' + element[2]['from'];
       pictureListFragment.appendChild(newPicture);
    });

    picturesList.appendChild(pictureListFragment);
};


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
    data.forEach((element) => {
       const newPicture = pictureTemplate.cloneNode(true);
       newPicture.querySelector('.name').textContent = element[0];
       newPicture.querySelector('.employer').textContent = element[1];
       newPicture.querySelector('.salary').textContent = [element[2]['from'], element[2]['to']]
           .filter((x) => !(x === null))
           .join("-") + " " + element[2]['currency'] + " " + {true: '(Без вычета налогов)', false: '(С вычетом налогов)', null: ''}[element[2]['gross']];
       newPicture.querySelector('.area').textContent = element[3];
       newPicture.querySelector('.published_at').textContent = element[4];
       newPicture.querySelector('.description').innerHTML = element[5];
       newPicture.querySelector('.key_skills').textContent = element[6].map((elem) => elem["name"]).join("; ");
       pictureListFragment.appendChild(newPicture);
    });

    picturesList.appendChild(pictureListFragment);
};

